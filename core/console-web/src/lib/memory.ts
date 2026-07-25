import fs from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";

export const MEMORY_ROOT =
  process.env.AIOS_MEMORY_ROOT ?? "/opt/ai-os/memory";

export const MEMORY_DB_PATH =
  process.env.AIOS_MEMORY_DB ?? path.join(MEMORY_ROOT, "memory.db");

/** Cursor-Projektordner unter ~/.cursor/projects/<id> — haengt vom
 * Workspace-Root ab (core/capture/cursor-job.mjs `projectIdFromPath`) und
 * aendert sich mit ihm; war lange auf den alten Scope "...-1100-AI-OS-V2"
 * fixiert, seit der Workspace-Root Projekte/ ist heisst er "home-peter-Projekte". */
export const DEFAULT_MEMORY_PROJECT =
  process.env.AIOS_MEMORY_PROJECT ?? "home-peter-Projekte";

export type MemoryChunk = {
  id: string;
  source: string;
  project_id: string;
  chat_id: string;
  role: string;
  title: string;
  body: string;
  source_path: string;
  created_at: string;
  ingested_at: string;
};

let dbSingleton: Database.Database | null = null;

export function projectLabel(projectId: string): string {
  return projectId
    .replace(/^home-peter-Projekte-/, "")
    .replace(/^home-peter-/, "");
}

export function projectIdFromSourcePath(filePath: string): string {
  const normalized = filePath.replace(/\\/g, "/");
  const marker = "/projects/";
  const i = normalized.indexOf(marker);
  if (i < 0) return "unknown";
  const rest = normalized.slice(i + marker.length);
  return rest.split("/").filter(Boolean)[0] ?? "unknown";
}

export function ensureMemoryDirs() {
  fs.mkdirSync(path.join(MEMORY_ROOT, "projects"), { recursive: true });
  fs.mkdirSync(path.join(MEMORY_ROOT, "state"), { recursive: true });
}

function migrate(db: Database.Database) {
  const cols = db.prepare(`PRAGMA table_info(chunks)`).all() as {
    name: string;
  }[];
  if (!cols.some((c) => c.name === "project_id")) {
    db.exec(
      `ALTER TABLE chunks ADD COLUMN project_id TEXT NOT NULL DEFAULT 'unknown'`,
    );
  }
  const rows = db
    .prepare(
      `SELECT id, source_path FROM chunks WHERE project_id = 'unknown' OR project_id = ''`,
    )
    .all() as { id: string; source_path: string }[];
  const upd = db.prepare(`UPDATE chunks SET project_id = ? WHERE id = ?`);
  for (const r of rows) {
    upd.run(projectIdFromSourcePath(r.source_path), r.id);
  }
  db.exec(
    `CREATE INDEX IF NOT EXISTS idx_chunks_project_ingested ON chunks(project_id, ingested_at)`,
  );
}

export function getMemoryDb(): Database.Database {
  if (dbSingleton) return dbSingleton;
  ensureMemoryDirs();
  const db = new Database(MEMORY_DB_PATH);
  db.pragma("journal_mode = WAL");
  db.exec(`
    CREATE TABLE IF NOT EXISTS chunks (
      id TEXT PRIMARY KEY,
      source TEXT NOT NULL,
      project_id TEXT NOT NULL DEFAULT 'unknown',
      chat_id TEXT NOT NULL,
      role TEXT NOT NULL,
      title TEXT NOT NULL DEFAULT '',
      body TEXT NOT NULL,
      source_path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      ingested_at TEXT NOT NULL
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
      title,
      body,
      source,
      chat_id,
      content='chunks',
      content_rowid='rowid'
    );
    CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
      INSERT INTO chunks_fts(rowid, title, body, source, chat_id)
      VALUES (new.rowid, new.title, new.body, new.source, new.chat_id);
    END;
    CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
      INSERT INTO chunks_fts(chunks_fts, rowid, title, body, source, chat_id)
      VALUES ('delete', old.rowid, old.title, old.body, old.source, old.chat_id);
    END;
    CREATE TABLE IF NOT EXISTS ingest_files (
      path TEXT PRIMARY KEY,
      mtime_ms INTEGER NOT NULL,
      size INTEGER NOT NULL,
      last_offset INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS capture_meta (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
  `);
  migrate(db);
  dbSingleton = db;
  return db;
}

function escapeFts(query: string): string {
  return query
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => `"${t.replace(/"/g, '""')}"`)
    .join(" AND ");
}

const SELECT_COLS = `c.id, c.source, c.project_id, c.chat_id, c.role, c.title, c.body, c.source_path, c.created_at, c.ingested_at`;

export function searchMemory(
  query: string,
  limit = 20,
  projectId: string | null = DEFAULT_MEMORY_PROJECT,
): MemoryChunk[] {
  const q = query.trim();
  if (!q) return [];
  const db = getMemoryDb();
  const fts = escapeFts(q);
  try {
    if (projectId) {
      return db
        .prepare(
          `SELECT ${SELECT_COLS}
           FROM chunks_fts f
           JOIN chunks c ON c.rowid = f.rowid
           WHERE chunks_fts MATCH ? AND c.project_id = ?
           ORDER BY rank
           LIMIT ?`,
        )
        .all(fts, projectId, limit) as MemoryChunk[];
    }
    return db
      .prepare(
        `SELECT ${SELECT_COLS}
         FROM chunks_fts f
         JOIN chunks c ON c.rowid = f.rowid
         WHERE chunks_fts MATCH ?
         ORDER BY rank
         LIMIT ?`,
      )
      .all(fts, limit) as MemoryChunk[];
  } catch {
    const like = `%${q}%`;
    if (projectId) {
      return db
        .prepare(
          `SELECT id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at
           FROM chunks
           WHERE project_id = ? AND (body LIKE ? OR title LIKE ?)
           ORDER BY ingested_at DESC LIMIT ?`,
        )
        .all(projectId, like, like, limit) as MemoryChunk[];
    }
    return db
      .prepare(
        `SELECT id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at
         FROM chunks
         WHERE body LIKE ? OR title LIKE ?
         ORDER BY ingested_at DESC LIMIT ?`,
      )
      .all(like, like, limit) as MemoryChunk[];
  }
}

export function memoryStats(projectId: string | null = DEFAULT_MEMORY_PROJECT) {
  const db = getMemoryDb();
  const scoped = Boolean(projectId);
  const chunks = (
    scoped
      ? (db
          .prepare(`SELECT COUNT(*) AS n FROM chunks WHERE project_id = ?`)
          .get(projectId) as { n: number })
      : (db.prepare(`SELECT COUNT(*) AS n FROM chunks`).get() as { n: number })
  ).n;
  const chats = (
    scoped
      ? (db
          .prepare(
            `SELECT COUNT(DISTINCT chat_id) AS n FROM chunks WHERE project_id = ?`,
          )
          .get(projectId) as { n: number })
      : (db
          .prepare(`SELECT COUNT(DISTINCT chat_id) AS n FROM chunks`)
          .get() as { n: number })
  ).n;
  const last = db
    .prepare(`SELECT value FROM capture_meta WHERE key = 'last_run_at'`)
    .get() as { value: string } | undefined;
  const lastFiles = (
    db.prepare(`SELECT COUNT(*) AS n FROM ingest_files`).get() as { n: number }
  ).n;
  const projects = db
    .prepare(
      `SELECT project_id AS id, COUNT(*) AS n FROM chunks GROUP BY project_id ORDER BY n DESC`,
    )
    .all() as { id: string; n: number }[];

  return {
    chunks,
    chats,
    trackedFiles: lastFiles,
    lastRunAt: last?.value ?? null,
    dbPath: MEMORY_DB_PATH,
    projectId: projectId ?? "all",
    projectLabel: projectId ? projectLabel(projectId) : "alle",
    projects,
  };
}

export function upsertChunk(chunk: MemoryChunk) {
  const db = getMemoryDb();
  db.prepare(
    `INSERT INTO chunks (id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at)
     VALUES (@id, @source, @project_id, @chat_id, @role, @title, @body, @source_path, @created_at, @ingested_at)
     ON CONFLICT(id) DO UPDATE SET
       body=excluded.body,
       title=excluded.title,
       project_id=excluded.project_id,
       ingested_at=excluded.ingested_at`,
  ).run(chunk);
}

export function setCaptureMeta(key: string, value: string) {
  getMemoryDb()
    .prepare(
      `INSERT INTO capture_meta(key, value) VALUES (?, ?)
       ON CONFLICT(key) DO UPDATE SET value=excluded.value`,
    )
    .run(key, value);
}
