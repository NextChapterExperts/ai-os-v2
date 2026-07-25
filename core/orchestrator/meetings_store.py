"""Meeting-Inbox — manuelle Erfassung (SQLite), optional ohne Projekt-Zuordnung."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .brain_store import list_engagements

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_ROOT = Path(os.environ.get("AIOS_ACTIVE_ROOT", REPO_ROOT.parent / "active"))
MEMORY_ROOT = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory"))
DB_PATH = Path(os.environ.get("AIOS_MEETINGS_DB", MEMORY_ROOT / "state" / "meetings.db"))
ATTACHMENTS_ROOT = Path(
    os.environ.get("AIOS_MEETINGS_ATTACHMENTS_DIR", MEMORY_ROOT / "state" / "meetings" / "attachments")
)
MAX_ATTACHMENT_BYTES = int(os.environ.get("AIOS_MEETING_ATTACHMENT_MAX_BYTES", str(25 * 1024 * 1024)))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    held_at TEXT NOT NULL,
    participants TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    engagement_ids TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    todos TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_meetings_tenant_held ON meetings(tenant_id, held_at DESC);

CREATE TABLE IF NOT EXISTS meeting_attachments (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_meeting_attachments_meeting ON meeting_attachments(meeting_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    return con


def _parse_json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^\w.\- ()]", "_", base).strip()
    return (cleaned[:200] or "attachment")


def _attachment_dir(meeting_id: str) -> Path:
    safe = meeting_id.replace("/", "_").replace("..", "_")
    return ATTACHMENTS_ROOT / safe


def _list_attachments_for(meeting_id: str, tenant_id: str) -> list[dict[str, Any]]:
    con = _connect()
    try:
        rows = con.execute(
            """
            SELECT id, filename, mime_type, size_bytes, created_at
            FROM meeting_attachments
            WHERE meeting_id = ? AND tenant_id = ?
            ORDER BY created_at ASC
            """,
            (meeting_id, tenant_id),
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "id": r["id"],
            "filename": r["filename"],
            "mime_type": r["mime_type"],
            "size_bytes": r["size_bytes"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def _row_to_dict(row: sqlite3.Row, *, tenant_id: str | None = None) -> dict[str, Any]:
    todos = _parse_json_list(row["todos"])
    open_todos = sum(1 for t in todos if isinstance(t, dict) and not t.get("done"))
    tid = tenant_id or row["tenant_id"]
    attachments = _list_attachments_for(row["id"], tid)
    return {
        "id": row["id"],
        "tenant_id": row["tenant_id"],
        "title": row["title"],
        "held_at": row["held_at"],
        "participants": row["participants"],
        "summary": row["summary"],
        "engagement_ids": _parse_json_list(row["engagement_ids"]),
        "tags": _parse_json_list(row["tags"]),
        "todos": todos,
        "open_todo_count": open_todos,
        "attachments": attachments,
        "attachment_count": len(attachments),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _read_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        m = re.match(r"^([a-zA-Z0-9_]+):\s*(.+)$", line.strip())
        if m:
            val = m.group(2).strip().strip('"').strip("'")
            out[m.group(1)] = val
    return out


def list_engagement_options() -> list[dict[str, str]]:
    """Engagements aus Brain-Seed + active/*/README.md für UI-Auswahl."""
    by_id: dict[str, dict[str, str]] = {}
    for e in list_engagements():
        eid = str(e.get("id") or "")
        if eid:
            by_id[eid] = {"id": eid, "title": str(e.get("title") or eid)}
    if ACTIVE_ROOT.is_dir():
        for readme in sorted(ACTIVE_ROOT.glob("*/README.md")):
            fm = _read_frontmatter(readme)
            eid = fm.get("id", "")
            if eid and eid.startswith("eng:"):
                by_id[eid] = {
                    "id": eid,
                    "title": fm.get("title") or readme.parent.name,
                }
    return sorted(by_id.values(), key=lambda x: x["title"].lower())


def list_meetings(
    tenant_id: str,
    *,
    q: str | None = None,
    unassigned: bool = False,
    has_open_todo: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    con = _connect()
    try:
        sql = "SELECT * FROM meetings WHERE tenant_id = ?"
        params: list[Any] = [tenant_id]
        if q:
            like = f"%{q.strip()}%"
            sql += (
                " AND (title LIKE ? OR participants LIKE ? OR summary LIKE ? OR tags LIKE ?"
                " OR id IN (SELECT meeting_id FROM meeting_attachments"
                " WHERE tenant_id = ? AND filename LIKE ?))"
            )
            params.extend([like, like, like, like, tenant_id, like])
        sql += " ORDER BY held_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()

    items = [_row_to_dict(r) for r in rows]
    if unassigned:
        items = [m for m in items if not m.get("engagement_ids")]
    if has_open_todo:
        items = [m for m in items if m.get("open_todo_count", 0) > 0]
    return items


def get_meeting(meeting_id: str, tenant_id: str) -> dict[str, Any] | None:
    con = _connect()
    try:
        row = con.execute(
            "SELECT * FROM meetings WHERE id = ? AND tenant_id = ?",
            (meeting_id, tenant_id),
        ).fetchone()
    finally:
        con.close()
    return _row_to_dict(row) if row else None


def create_meeting(tenant_id: str, data: dict[str, Any]) -> dict[str, Any]:
    meeting_id = str(data.get("id") or f"meet-{uuid.uuid4().hex[:12]}")
    now = _now()
    row = {
        "id": meeting_id,
        "tenant_id": tenant_id,
        "title": str(data.get("title") or "").strip(),
        "held_at": str(data.get("held_at") or now),
        "participants": str(data.get("participants") or "").strip(),
        "summary": str(data.get("summary") or "").strip(),
        "engagement_ids": json.dumps(data.get("engagement_ids") or [], ensure_ascii=False),
        "tags": json.dumps(data.get("tags") or [], ensure_ascii=False),
        "todos": json.dumps(data.get("todos") or [], ensure_ascii=False),
        "created_at": now,
        "updated_at": now,
    }
    if not row["title"]:
        raise ValueError("title required")

    con = _connect()
    try:
        con.execute(
            """
            INSERT INTO meetings (
                id, tenant_id, title, held_at, participants, summary,
                engagement_ids, tags, todos, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :title, :held_at, :participants, :summary,
                :engagement_ids, :tags, :todos, :created_at, :updated_at
            )
            """,
            row,
        )
        con.commit()
    finally:
        con.close()
    return get_meeting(meeting_id, tenant_id) or row


def update_meeting(meeting_id: str, tenant_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_meeting(meeting_id, tenant_id)
    if not existing:
        return None

    fields: dict[str, Any] = {
        "title": str(data.get("title", existing["title"])).strip(),
        "held_at": str(data.get("held_at", existing["held_at"])),
        "participants": str(data.get("participants", existing["participants"])).strip(),
        "summary": str(data.get("summary", existing["summary"])).strip(),
        "engagement_ids": json.dumps(
            data.get("engagement_ids", existing["engagement_ids"]), ensure_ascii=False
        ),
        "tags": json.dumps(data.get("tags", existing["tags"]), ensure_ascii=False),
        "todos": json.dumps(data.get("todos", existing["todos"]), ensure_ascii=False),
        "updated_at": _now(),
        "id": meeting_id,
        "tenant_id": tenant_id,
    }
    if not fields["title"]:
        raise ValueError("title required")

    con = _connect()
    try:
        con.execute(
            """
            UPDATE meetings SET
                title = :title,
                held_at = :held_at,
                participants = :participants,
                summary = :summary,
                engagement_ids = :engagement_ids,
                tags = :tags,
                todos = :todos,
                updated_at = :updated_at
            WHERE id = :id AND tenant_id = :tenant_id
            """,
            fields,
        )
        con.commit()
    finally:
        con.close()
    return get_meeting(meeting_id, tenant_id)


def delete_meeting(meeting_id: str, tenant_id: str) -> bool:
    con = _connect()
    try:
        cur = con.execute(
            "DELETE FROM meetings WHERE id = ? AND tenant_id = ?",
            (meeting_id, tenant_id),
        )
        con.execute(
            "DELETE FROM meeting_attachments WHERE meeting_id = ? AND tenant_id = ?",
            (meeting_id, tenant_id),
        )
        con.commit()
        deleted = cur.rowcount > 0
    finally:
        con.close()
    if deleted:
        att_dir = _attachment_dir(meeting_id)
        if att_dir.is_dir():
            for p in att_dir.iterdir():
                if p.is_file():
                    p.unlink(missing_ok=True)
            att_dir.rmdir()
    return deleted


def add_attachment(
    meeting_id: str,
    tenant_id: str,
    *,
    filename: str,
    content: bytes,
    mime_type: str | None = None,
) -> dict[str, Any]:
    if not get_meeting(meeting_id, tenant_id):
        raise ValueError("meeting not found")
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise ValueError(f"file too large (max {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB)")

    att_id = f"att-{uuid.uuid4().hex[:12]}"
    safe_name = _safe_filename(filename)
    stored_name = f"{att_id}_{safe_name}"
    dest_dir = _attachment_dir(meeting_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / stored_name
    dest_path.write_bytes(content)

    now = _now()
    row = {
        "id": att_id,
        "meeting_id": meeting_id,
        "tenant_id": tenant_id,
        "filename": safe_name,
        "stored_name": stored_name,
        "mime_type": (mime_type or "application/octet-stream").split(";")[0].strip(),
        "size_bytes": len(content),
        "created_at": now,
    }
    con = _connect()
    try:
        con.execute(
            """
            INSERT INTO meeting_attachments (
                id, meeting_id, tenant_id, filename, stored_name,
                mime_type, size_bytes, created_at
            ) VALUES (
                :id, :meeting_id, :tenant_id, :filename, :stored_name,
                :mime_type, :size_bytes, :created_at
            )
            """,
            row,
        )
        con.execute(
            "UPDATE meetings SET updated_at = ? WHERE id = ? AND tenant_id = ?",
            (now, meeting_id, tenant_id),
        )
        con.commit()
    finally:
        con.close()
    return {
        "id": att_id,
        "filename": safe_name,
        "mime_type": row["mime_type"],
        "size_bytes": len(content),
        "created_at": now,
    }


def get_attachment_path(
    meeting_id: str,
    attachment_id: str,
    tenant_id: str,
) -> tuple[Path, dict[str, Any]] | None:
    con = _connect()
    try:
        row = con.execute(
            """
            SELECT * FROM meeting_attachments
            WHERE id = ? AND meeting_id = ? AND tenant_id = ?
            """,
            (attachment_id, meeting_id, tenant_id),
        ).fetchone()
    finally:
        con.close()
    if not row:
        return None
    path = _attachment_dir(meeting_id) / row["stored_name"]
    if not path.is_file():
        return None
    meta = {
        "id": row["id"],
        "filename": row["filename"],
        "mime_type": row["mime_type"],
        "size_bytes": row["size_bytes"],
    }
    return path, meta


def delete_attachment(meeting_id: str, attachment_id: str, tenant_id: str) -> bool:
    con = _connect()
    try:
        row = con.execute(
            """
            SELECT stored_name FROM meeting_attachments
            WHERE id = ? AND meeting_id = ? AND tenant_id = ?
            """,
            (attachment_id, meeting_id, tenant_id),
        ).fetchone()
        if not row:
            return False
        con.execute(
            "DELETE FROM meeting_attachments WHERE id = ? AND meeting_id = ? AND tenant_id = ?",
            (attachment_id, meeting_id, tenant_id),
        )
        con.execute(
            "UPDATE meetings SET updated_at = ? WHERE id = ? AND tenant_id = ?",
            (_now(), meeting_id, tenant_id),
        )
        con.commit()
        stored_name = row["stored_name"]
    finally:
        con.close()
    path = _attachment_dir(meeting_id) / stored_name
    if path.is_file():
        path.unlink()
    return True
