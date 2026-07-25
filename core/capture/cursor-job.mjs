#!/usr/bin/env node
/**
 * Cursor Chat Capture
 * Pollt ~/.cursor/projects/<project>/agent-transcripts/*.jsonl
 * und schreibt Turns projektbezogen ins Gedächtnis (SQLite FTS).
 *
 * Usage:
 *   node cursor-job.mjs              # Dauerloop (10s)
 *   node cursor-job.mjs --once       # einmalig
 *   node cursor-job.mjs --reindex    # Dateien erneut einlesen (project_id)
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import os from "node:os";
import Database from "better-sqlite3";

const MEMORY_ROOT = process.env.AIOS_MEMORY_ROOT ?? "/opt/ai-os/memory";
const MEMORY_DB = process.env.AIOS_MEMORY_DB ?? path.join(MEMORY_ROOT, "memory.db");
const CURSOR_PROJECTS =
  process.env.CURSOR_PROJECTS_ROOT ??
  path.join(os.homedir(), ".cursor", "projects");
const INTERVAL_MS = Number(process.env.CAPTURE_INTERVAL_MS ?? 10000);
const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL ?? "http://127.0.0.1:8091";
const ONCE = process.argv.includes("--once");
const REINDEX = process.argv.includes("--reindex");

function projectIdFromPath(filePath) {
  const normalized = filePath.replace(/\\/g, "/");
  const marker = "/projects/";
  const i = normalized.indexOf(marker);
  if (i < 0) return "unknown";
  const rest = normalized.slice(i + marker.length);
  return rest.split("/").filter(Boolean)[0] ?? "unknown";
}

function ensureDirs() {
  fs.mkdirSync(path.join(MEMORY_ROOT, "projects"), { recursive: true });
  fs.mkdirSync(path.join(MEMORY_ROOT, "state"), { recursive: true });
}

function openDb() {
  ensureDirs();
  const db = new Database(MEMORY_DB);
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
      title, body, source, chat_id,
      content='chunks', content_rowid='rowid'
    );
    CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
      INSERT INTO chunks_fts(rowid, title, body, source, chat_id)
      VALUES (new.rowid, new.title, new.body, new.source, new.chat_id);
    END;
    CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
      INSERT INTO chunks_fts(chunks_fts, rowid, title, body, source, chat_id)
      VALUES ('delete', old.rowid, old.title, old.body, old.source, old.chat_id);
    END;
    CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
      INSERT INTO chunks_fts(chunks_fts, rowid, title, body, source, chat_id)
      VALUES ('delete', old.rowid, old.title, old.body, old.source, old.chat_id);
      INSERT INTO chunks_fts(rowid, title, body, source, chat_id)
      VALUES (new.rowid, new.title, new.body, new.source, new.chat_id);
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
    CREATE INDEX IF NOT EXISTS idx_chunks_project_ingested
      ON chunks(project_id, ingested_at);
  `);

  const cols = db.prepare(`PRAGMA table_info(chunks)`).all();
  if (!cols.some((c) => c.name === "project_id")) {
    db.exec(
      `ALTER TABLE chunks ADD COLUMN project_id TEXT NOT NULL DEFAULT 'unknown'`,
    );
  }

  // Backfill project_id from path
  const rows = db
    .prepare(
      `SELECT id, source_path FROM chunks WHERE project_id = 'unknown' OR project_id = ''`,
    )
    .all();
  const upd = db.prepare(`UPDATE chunks SET project_id = ? WHERE id = ?`);
  for (const r of rows) {
    upd.run(projectIdFromPath(r.source_path), r.id);
  }

  if (REINDEX) {
    db.exec(`DELETE FROM ingest_files`);
    console.log("[capture] reindex: ingest_files geleert");
  }

  return db;
}

function extractText(message) {
  if (!message) return "";
  const content = message.content;
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content
    .filter((p) => p && p.type === "text" && typeof p.text === "string")
    .map((p) => p.text)
    .join("\n")
    .trim();
}

function cleanUserText(text) {
  let t = text;
  const q = t.match(/<user_query>\s*([\s\S]*?)\s*<\/user_query>/i);
  if (q) t = q[1];
  t = t.replace(/<\/?timestamp[^>]*>/gi, "").trim();
  return t;
}

function walkJsonl(root) {
  const out = [];
  if (!fs.existsSync(root)) return out;
  const stack = [root];
  while (stack.length) {
    const dir = stack.pop();
    let entries = [];
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const ent of entries) {
      const full = path.join(dir, ent.name);
      if (ent.isDirectory()) stack.push(full);
      else if (ent.isFile() && ent.name.endsWith(".jsonl")) out.push(full);
    }
  }
  return out;
}

function chatIdFromPath(filePath) {
  return path.basename(filePath, ".jsonl");
}

function upsertChunk(db, chunk) {
  db.prepare(
    `INSERT INTO chunks (id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at)
     VALUES (@id, @source, @project_id, @chat_id, @role, @title, @body, @source_path, @created_at, @ingested_at)
     ON CONFLICT(id) DO UPDATE SET
       body=excluded.body, title=excluded.title, project_id=excluded.project_id,
       ingested_at=excluded.ingested_at`,
  ).run(chunk);
}

function setMeta(db, key, value) {
  db.prepare(
    `INSERT INTO capture_meta(key, value) VALUES (?, ?)
     ON CONFLICT(key) DO UPDATE SET value=excluded.value`,
  ).run(key, value);
}

function ingestFile(db, filePath) {
  const st = fs.statSync(filePath);
  const prev = db
    .prepare(`SELECT mtime_ms, size, last_offset FROM ingest_files WHERE path = ?`)
    .get(filePath);

  if (
    prev &&
    prev.mtime_ms === Math.floor(st.mtimeMs) &&
    prev.size === st.size &&
    prev.last_offset >= st.size
  ) {
    return 0;
  }

  const projectId = projectIdFromPath(filePath);
  const raw = fs.readFileSync(filePath, "utf8");
  const chatId = chatIdFromPath(filePath);
  const lines = raw.split("\n").filter((l) => l.trim());
  let inserted = 0;
  const now = new Date().toISOString();
  const archiveLines = [];

  lines.forEach((line, idx) => {
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      return;
    }
    const role = obj.role || "unknown";
    let body = extractText(obj.message);
    if (!body) return;
    if (role === "user") body = cleanUserText(body);
    if (body.length < 8) return;
    if (body.length > 12000) body = body.slice(0, 12000) + "\n…[gekürzt]";

    const id = crypto
      .createHash("sha256")
      .update(`${filePath}:${idx}:${role}:${body.slice(0, 200)}`)
      .digest("hex")
      .slice(0, 32);

    const title =
      role === "user"
        ? body.slice(0, 80).replace(/\s+/g, " ")
        : `Antwort · ${chatId.slice(0, 8)}`;

    upsertChunk(db, {
      id,
      source: "cursor",
      project_id: projectId,
      chat_id: chatId,
      role,
      title,
      body,
      source_path: filePath,
      created_at: now,
      ingested_at: now,
    });
    archiveLines.push(`### ${role}\n\n${body}\n`);
    inserted += 1;
  });

  const projDir = path.join(MEMORY_ROOT, "projects", projectId, "cursor");
  fs.mkdirSync(projDir, { recursive: true });
  fs.writeFileSync(
    path.join(projDir, `${chatId}.md`),
    `# Cursor Chat ${chatId}\n\nProjekt: ${projectId}\nQuelle: \`${filePath}\`\n\n${archiveLines.join("\n")}`,
    "utf8",
  );

  db.prepare(
    `INSERT INTO ingest_files(path, mtime_ms, size, last_offset, updated_at)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(path) DO UPDATE SET
       mtime_ms=excluded.mtime_ms,
       size=excluded.size,
       last_offset=excluded.last_offset,
       updated_at=excluded.updated_at`,
  ).run(filePath, Math.floor(st.mtimeMs), st.size, st.size, now);

  return inserted;
}

async function syncLettaIfNeeded(upserts) {
  if (upserts <= 0) return;
  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/v1/memory/sync-letta`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tenant_id: "nextchapter", source: "cursor" }),
      signal: AbortSignal.timeout(120_000),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.warn(`[capture] letta-sync HTTP ${res.status}: ${text.slice(0, 120)}`);
      return;
    }
    const data = await res.json();
    if (data.synced > 0) {
      console.log(`[capture] letta-sync synced=${data.synced} skipped=${data.skipped}`);
    }
  } catch (err) {
    console.warn("[capture] letta-sync:", err.message || err);
  }
}

function runOnce(db) {
  const files = walkJsonl(CURSOR_PROJECTS);
  let total = 0;
  const byProject = {};
  for (const f of files) {
    try {
      const n = ingestFile(db, f);
      total += n;
      const pid = projectIdFromPath(f);
      byProject[pid] = (byProject[pid] || 0) + 1;
    } catch (err) {
      console.error(`[capture] Fehler bei ${f}:`, err.message || err);
    }
  }
  setMeta(db, "last_run_at", new Date().toISOString());
  setMeta(db, "last_files_seen", String(files.length));
  const count = db.prepare(`SELECT COUNT(*) AS n FROM chunks`).get().n;
  console.log(
    `[capture] files=${files.length} upserts≈${total} chunks=${count} projects=${JSON.stringify(byProject)}`,
  );
  return { files: files.length, upserts: total, chunks: count };
}

function main() {
  const db = openDb();
  console.log(`[capture] watching ${CURSOR_PROJECTS} → ${MEMORY_DB}`);
  void syncLettaIfNeeded(runOnce(db).upserts ?? 0);
  if (ONCE || REINDEX) {
    db.close();
    return;
  }
  setInterval(() => {
    try {
      const stats = runOnce(db);
      void syncLettaIfNeeded(stats?.upserts ?? 0);
    } catch (err) {
      console.error("[capture] loop error:", err.message || err);
    }
  }, INTERVAL_MS);
}

main();
