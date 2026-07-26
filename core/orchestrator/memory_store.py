"""Zugriff auf die Cursor-Capture-SQLite (memory.db) — gemeinsam genutzt von
`handlers/memory_ask.py` (Lagebild-Ask) und `handlers/unified_search.py`
(episodischer Fallback bzw. Merge mit Letta L2).

Der Projekt-Slug haengt vom Cursor-Workspace-Pfad ab
(core/capture/cursor-job.mjs `projectIdFromPath`) und aendert sich, wenn sich
der Workspace-Root aendert (z.B. Projekte/1100-AI-OS-V2 -> Projekte/). Beide
Abfrage-Funktionen fallen deshalb auf projektuebergreifende Suche zurueck,
statt wegen eines veralteten Slugs 0 Treffer zu liefern.
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from core.memory_gateway.sqlite_schema import ensure_schema

MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")
# War lange auf den alten Workspace-Scope "...-1100-AI-OS-V2" fixiert; seit der
# Workspace-Root Projekte/ ist, lauten neue Chunks auf "home-peter-Projekte".
DEFAULT_PROJECT = os.environ.get("AIOS_MEMORY_PROJECT", "home-peter-Projekte")


def _day_bounds(offset_days: int) -> tuple[str, str]:
    tz = ZoneInfo("Europe/Berlin")
    now = datetime.now(tz)
    start = (now + timedelta(days=offset_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()


def resolve_window(question: str) -> tuple[str, str, str]:
    """(start, end, mode) — Keyword-Heuristik (P4), kein NLU/LLM.

    Bisher fragte memory_ask IMMER nur "heute" ab, unabhaengig davon, ob die
    Frage "gestern" enthielt — daher 0 Treffer bei "was haben wir gestern
    gemacht?". Jetzt: "gestern" -> Vortag, "letzte/diese Woche" -> 7-Tage-
    Fenster, sonst Default "heute".
    """
    lower = (question or "").lower()
    if "gestern" in lower:
        start, end = _day_bounds(-1)
        return start, end, "yesterday"
    if any(k in lower for k in ("letzte woche", "diese woche", "vorletzte woche")):
        start, _ = _day_bounds(-7)
        _, end = _day_bounds(0)
        return start, end, "week"
    start, end = _day_bounds(0)
    return start, end, "today"


def chunks_in_window(
    project_id: str | None,
    start: str,
    end: str,
    limit: int = 40,
    role: str | None = "user",
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Chunks in [start, end), optional auf `project_id` + `role` + `user_id`/`visibility` eingeschraenkt."""
    if not os.path.exists(MEMORY_DB):
        return []
    uid = user_id or "default_user"
    con = sqlite3.connect(MEMORY_DB)
    con.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(chunks)")}
        has_project_col = "project_id" in cols
        has_user_col = "user_id" in cols

        def _query(with_project: bool) -> list[dict[str, Any]]:
            sql = (
                "SELECT id, role, title, body, chat_id, source, ingested_at, project_id, user_id, visibility "
                "FROM chunks WHERE ingested_at >= ? AND ingested_at < ?"
            )
            params: list[Any] = [start, end]
            if role:
                sql += " AND role = ?"
                params.append(role)
            if has_user_col:
                sql += " AND (visibility = 'company' OR (visibility = 'team' AND (project_id IS NULL OR project_id = ?)) OR (visibility = 'private' AND user_id = ?))"
                params.extend([project_id or DEFAULT_PROJECT, uid])
            elif with_project and has_project_col and project_id:
                sql += " AND project_id = ?"
                params.append(project_id)
            sql += " ORDER BY ingested_at ASC LIMIT ?"
            params.append(limit)
            return [dict(r) for r in con.execute(sql, params).fetchall()]

        rows = _query(with_project=True)
        if not rows and project_id:
            rows = _query(with_project=False)
        return rows
    finally:
        con.close()


def search_chunks(
    query: str,
    project_id: str | None = None,
    limit: int = 10,
    since_days: int = 30,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Freitext (LIKE) ueber Chunk-Titel/-Body der letzten `since_days` Tage."""
    q = (query or "").strip()
    if not os.path.exists(MEMORY_DB) or not q:
        return []
    uid = user_id or "default_user"
    tz = ZoneInfo("Europe/Berlin")
    since = (datetime.now(tz) - timedelta(days=since_days)).astimezone(timezone.utc).isoformat()
    like = f"%{q}%"
    con = sqlite3.connect(MEMORY_DB)
    con.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(chunks)")}
        has_project_col = "project_id" in cols
        has_user_col = "user_id" in cols

        def _query(with_project: bool) -> list[dict[str, Any]]:
            sql = (
                "SELECT id, role, title, body, chat_id, source, ingested_at, project_id, user_id, visibility "
                "FROM chunks WHERE ingested_at >= ? AND (body LIKE ? OR title LIKE ?)"
            )
            params: list[Any] = [since, like, like]
            if has_user_col:
                sql += " AND (visibility = 'company' OR (visibility = 'team' AND (project_id IS NULL OR project_id = ?)) OR (visibility = 'private' AND user_id = ?))"
                params.extend([project_id or DEFAULT_PROJECT, uid])
            elif with_project and has_project_col and project_id:
                sql += " AND project_id = ?"
                params.append(project_id)
            sql += " ORDER BY ingested_at DESC LIMIT ?"
            params.append(limit)
            return [dict(r) for r in con.execute(sql, params).fetchall()]

        rows = _query(with_project=True)
        if not rows and project_id:
            rows = _query(with_project=False)
        return rows
    finally:
        con.close()


def _escape_fts(query: str) -> str:
    tokens = [t for t in re.split(r"\W+", query.strip()) if len(t) >= 2]
    if not tokens:
        return ""
    return " AND ".join(f'"{t.replace(chr(34), "")}"' for t in tokens[:12])


def search_chunks_fts(
    query: str,
    project_id: str | None = None,
    limit: int = 10,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """FTS5-Suche über chunks_fts (schneller und genauer als LIKE)."""
    fts_q = _escape_fts(query)
    if not fts_q or not os.path.exists(MEMORY_DB):
        return []

    uid = user_id or "default_user"
    con = ensure_schema()
    con.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(chunks)")}
        has_project_col = "project_id" in cols
        has_user_col = "user_id" in cols

        def _query(with_project: bool) -> list[dict[str, Any]]:
            sql = (
                "SELECT c.id, c.role, c.title, c.body, c.chat_id, c.source, "
                "c.ingested_at, c.project_id, c.user_id, c.visibility, c.source_path "
                "FROM chunks_fts f JOIN chunks c ON c.rowid = f.rowid "
                "WHERE chunks_fts MATCH ?"
            )
            params: list[Any] = [fts_q]
            if has_user_col:
                sql += " AND (c.visibility = 'company' OR (c.visibility = 'team' AND (c.project_id IS NULL OR c.project_id = ?)) OR (c.visibility = 'private' AND c.user_id = ?))"
                params.extend([project_id or DEFAULT_PROJECT, uid])
            elif with_project and has_project_col and project_id:
                sql += " AND c.project_id = ?"
                params.append(project_id)
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            return [dict(r) for r in con.execute(sql, params).fetchall()]

        rows = _query(with_project=True)
        if not rows and project_id:
            rows = _query(with_project=False)
        return rows
    except sqlite3.OperationalError:
        return search_chunks(query, project_id=project_id, limit=limit, user_id=user_id)
    finally:
        con.close()
