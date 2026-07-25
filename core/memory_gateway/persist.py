"""Persist-Hook: LLM-Turns in memory.db (SQLite FTS) schreiben."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from .letta_client import insert_episode, is_available as letta_available

MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")
DEFAULT_PROJECT = os.environ.get("AIOS_MEMORY_PROJECT", "home-peter-Projekte")


def _chunk_id(chat_id: str, role: str, body: str) -> str:
    raw = f"{chat_id}:{role}:{body[:200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
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
        )
        """
    )


def persist_chat_turn(
    tenant_id: str,
    messages: list[dict[str, Any]],
    assistant_content: str,
    *,
    session_id: str,
    produced_by: str,
    model: str,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Speichert den letzten User-Turn + Assistant-Antwort in memory.db."""
    if not os.path.exists(MEMORY_DB):
        os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    pid = project_id or DEFAULT_PROJECT
    source_path = f"memory-gateway/{tenant_id}/{session_id}"
    written: list[str] = []

    last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    con = sqlite3.connect(MEMORY_DB)
    try:
        _ensure_schema(con)
        upsert = """
            INSERT INTO chunks (id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              body=excluded.body, title=excluded.title, ingested_at=excluded.ingested_at
        """
        if last_user:
            body = str(last_user.get("content") or "")
            cid = _chunk_id(session_id, "user", body)
            con.execute(
                upsert,
                (
                    cid,
                    "memory-gateway",
                    pid,
                    session_id,
                    "user",
                    body[:80],
                    body,
                    source_path,
                    now,
                    now,
                ),
            )
            written.append(cid)

        if assistant_content.strip():
            cid = _chunk_id(session_id, "assistant", assistant_content)
            con.execute(
                upsert,
                (
                    cid,
                    "memory-gateway",
                    pid,
                    session_id,
                    "assistant",
                    assistant_content[:80],
                    assistant_content,
                    source_path,
                    now,
                    now,
                ),
            )
            written.append(cid)

        con.commit()
    finally:
        con.close()

    letta_result: dict[str, Any] | None = None
    if letta_available() and last_user and assistant_content.strip():
        letta_result = insert_episode(
            tenant_id,
            str(last_user.get("content") or ""),
            produced_by,
            assistant_content,
        )

    return {
        "persisted": len(written),
        "chunk_ids": written,
        "session_id": session_id,
        "model": model,
        "produced_by": produced_by,
        "letta": letta_result,
    }
