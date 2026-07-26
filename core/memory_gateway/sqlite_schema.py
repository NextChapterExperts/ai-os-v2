"""Gemeinsames SQLite-Schema für memory.db (chunks + FTS5).

Wird von persist.py, chat_import.py und Rebuild-Skripten genutzt.
cursor-job.mjs und console/lib/memory.ts spiegeln dasselbe Schema (JS).
"""

from __future__ import annotations

import os
import sqlite3

MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    project_id TEXT NOT NULL DEFAULT 'unknown',
    user_id TEXT NOT NULL DEFAULT 'default_user',
    visibility TEXT NOT NULL DEFAULT 'team',
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
CREATE INDEX IF NOT EXISTS idx_chunks_project_ingested ON chunks(project_id, ingested_at);
CREATE INDEX IF NOT EXISTS idx_chunks_source_ingested ON chunks(source, ingested_at);
CREATE INDEX IF NOT EXISTS idx_chunks_user_visibility ON chunks(user_id, visibility);
"""


def ensure_schema(con: sqlite3.Connection | None = None) -> sqlite3.Connection:
    owns = con is None
    if owns:
        os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
        con = sqlite3.connect(MEMORY_DB)
    con.executescript(_SCHEMA_SQL)
    cols = {r[1] for r in con.execute("PRAGMA table_info(chunks)")}
    if "project_id" not in cols:
        con.execute("ALTER TABLE chunks ADD COLUMN project_id TEXT NOT NULL DEFAULT 'unknown'")
    if "user_id" not in cols:
        con.execute("ALTER TABLE chunks ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default_user'")
    if "visibility" not in cols:
        con.execute("ALTER TABLE chunks ADD COLUMN visibility TEXT NOT NULL DEFAULT 'team'")
    if owns:
        con.commit()
    return con


def rebuild_fts(con: sqlite3.Connection | None = None) -> dict[str, int]:
    """FTS-Index aus chunks neu aufbauen."""
    owns = con is None
    con = ensure_schema(con)
    before = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    con.commit()
    fts_count = con.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    if owns:
        con.close()
    return {"chunks": before, "fts_rows": fts_count}
