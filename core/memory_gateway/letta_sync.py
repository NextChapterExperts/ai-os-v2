"""SQLite chunks → Letta L2 Archival synchronisieren (Backfill + Live-Sync)."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .letta_client import format_archival_episode, insert_archival, is_available
from .sqlite_schema import MEMORY_DB, ensure_schema

log = logging.getLogger("letta_sync")

SYNC_STATE_PATH = Path(
    os.environ.get("LETTA_SYNC_STATE", "/opt/ai-os/memory/state/letta-sync.json")
)
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "nextchapter")


def _load_sync_state() -> dict[str, str]:
    if not SYNC_STATE_PATH.is_file():
        return {}
    try:
        return {str(k): str(v) for k, v in json.loads(SYNC_STATE_PATH.read_text()).items()}
    except Exception:
        return {}


def _save_sync_state(state: dict[str, str]) -> None:
    SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _fetch_chunks(
    con: sqlite3.Connection,
    *,
    since: str | None = None,
    source: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    con.row_factory = sqlite3.Row
    sql = (
        "SELECT id, source, project_id, chat_id, role, title, body, ingested_at "
        "FROM chunks WHERE 1=1"
    )
    params: list[Any] = []
    if since:
        sql += " AND ingested_at >= ?"
        params.append(since)
    if source:
        sql += " AND source = ?"
        params.append(source)
    sql += " ORDER BY ingested_at ASC, chat_id ASC, role ASC"
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def _pair_episodes(rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], str]]:
    """User-Turns mit optionaler Assistant-Antwort als Episoden-Paare."""
    by_chat: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_chat.setdefault(row["chat_id"], []).append(row)

    pairs: list[tuple[dict[str, Any], str]] = []
    for chat_rows in by_chat.values():
        for idx, row in enumerate(chat_rows):
            if row["role"] != "user":
                continue
            answer = ""
            if idx + 1 < len(chat_rows) and chat_rows[idx + 1]["role"] == "assistant":
                answer = str(chat_rows[idx + 1]["body"] or "")
            pairs.append((row, answer))
    return pairs


def sync_sqlite_to_letta(
    tenant_id: str = DEFAULT_TENANT,
    *,
    since: str | None = None,
    source: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Synchronisiert SQLite-Chunks nach Letta (idempotent via Sync-State)."""
    if not is_available():
        return {"ok": False, "error": "letta_unavailable", "synced": 0, "skipped": 0}

    if not os.path.exists(MEMORY_DB):
        return {"ok": False, "error": "memory_db_missing", "synced": 0, "skipped": 0}

    con = ensure_schema()
    try:
        rows = _fetch_chunks(con, since=since, source=source, limit=limit)
    finally:
        con.close()

    state = {} if force else _load_sync_state()
    synced = 0
    skipped = 0
    errors: list[str] = []

    for user_row, answer in _pair_episodes(rows):
        chunk_id = str(user_row["id"])
        if not force and chunk_id in state:
            skipped += 1
            continue

        ts_raw = str(user_row.get("ingested_at") or "")
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(timezone.utc)

        episode = format_archival_episode(
            str(user_row.get("body") or ""),
            str(user_row.get("source") or "sqlite"),
            answer,
            decision=f"chunk_id={chunk_id}",
            ts=ts,
        )

        if dry_run:
            synced += 1
            continue

        result = insert_archival(tenant_id, episode)
        if result.get("success"):
            state[chunk_id] = str(result.get("passage_id") or "ok")
            synced += 1
        else:
            errors.append(f"{chunk_id}: {result.get('error')}")
            skipped += 1

    if not dry_run and synced:
        _save_sync_state(state)

    return {
        "ok": len(errors) == 0,
        "synced": synced,
        "skipped": skipped,
        "errors": errors[:20],
        "total_candidates": len(rows),
        "tenant_id": tenant_id,
        "dry_run": dry_run,
    }
