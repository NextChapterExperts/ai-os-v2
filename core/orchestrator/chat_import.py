"""Chat-Import — externe Chats (Antigravity, Gemini, …) ins Gedächtnis (Phase 1b).

Normalisiert ein Transcript-Dict und schreibt:
1. Chunks in memory.db (SQLite FTS, wie Cursor-Capture)
2. Archiv-Markdown unter /opt/ai-os/ingest/inbox/chats/
3. Audit-Eintrag in ai_os_log (Hash-Chain)

Roh-Chat wird nicht als org:Claim behandelt (P18 / Roadmap 1b.6).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.memory_gateway.audit import write_llm_audit
from core.memory_gateway.letta_client import format_archival_episode, insert_archival, is_available as letta_available
from core.memory_gateway.sqlite_schema import ensure_schema

MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")
INBOX_ROOT = Path(os.environ.get("AIOS_INGEST_INBOX", "/opt/ai-os/ingest/inbox"))
DEFAULT_PROJECT = os.environ.get("AIOS_MEMORY_PROJECT", "home-peter-Projekte")

_ROLE_LABELS = {"user": "Nutzer", "assistant": "Assistent", "model": "Assistent"}


def _slug(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^\w\-]+", "-", (text or "").strip().lower()).strip("-")
    return s[:max_len] if s else "chat"


def _yaml_escape(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _chunk_id(chat_id: str, role: str, body: str, index: int) -> str:
    raw = f"{chat_id}:{index}:{role}:{body[:200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _normalize_messages(transcript: dict[str, Any]) -> list[dict[str, Any]]:
    messages = transcript.get("messages") or []
    if messages:
        out = []
        for msg in messages:
            role = str(msg.get("role") or "user").lower()
            if role == "model":
                role = "assistant"
            text = str(msg.get("text") or msg.get("content") or "").strip()
            if not text or len(text) < 4:
                continue
            out.append(
                {
                    "role": role,
                    "text": text[:12000],
                    "ts": msg.get("ts") or msg.get("created_at"),
                }
            )
        return out

    body = str(transcript.get("body") or "").strip()
    if body:
        return [{"role": "user", "text": body[:12000], "ts": None}]
    return []


def _render_markdown(transcript: dict[str, Any], messages: list[dict[str, Any]]) -> str:
    source = str(transcript.get("source") or "chat")
    title = str(transcript.get("title") or transcript.get("external_id") or "Chat")
    account = str(transcript.get("account_email") or transcript.get("account_id") or "")
    url = str(transcript.get("url") or "")
    now = datetime.now(timezone.utc).isoformat()

    fm = [
        "---",
        f"source: {_yaml_escape(source)}",
        f"external_id: {_yaml_escape(str(transcript.get('external_id') or ''))}",
        f"title: {_yaml_escape(title)}",
        f"captured_at: {_yaml_escape(str(transcript.get('captured_at') or now))}",
        "project: chats",
        "---",
        "",
        f"# {title}",
        "",
        f"> Quelle: {source}" + (f" · {account}" if account else "") + (f" · [Original]({url})" if url else ""),
        "",
    ]
    for msg in messages:
        label = _ROLE_LABELS.get(msg["role"], msg["role"])
        fm.append(f"**{label}:**\n\n{msg['text']}\n")
    return "\n".join(fm)


def _upsert_chunks(
    *,
    source: str,
    chat_id: str,
    messages: list[dict[str, Any]],
    source_path: str,
    project_id: str,
) -> list[str]:
    if not messages:
        return []
    os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    written: list[str] = []
    con = sqlite3.connect(MEMORY_DB)
    try:
        ensure_schema(con)
        upsert = """
            INSERT INTO chunks (id, source, project_id, chat_id, role, title, body, source_path, created_at, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              body=excluded.body, title=excluded.title, ingested_at=excluded.ingested_at
        """
        for idx, msg in enumerate(messages):
            body = msg["text"]
            role = msg["role"]
            cid = _chunk_id(chat_id, role, body, idx)
            title = body[:80] if role == "user" else f"Antwort · {chat_id[:8]}"
            ts = str(msg.get("ts") or now)
            con.execute(
                upsert,
                (cid, source, project_id, chat_id, role, title, body, source_path, ts, now),
            )
            written.append(cid)
        con.commit()
    finally:
        con.close()
    return written


def import_transcript(
    transcript: dict[str, Any],
    *,
    tenant_id: str = "nextchapter",
    project_id: str | None = None,
) -> dict[str, Any]:
    """Importiert ein normalisiertes Transcript ins Gedächtnis."""
    source = str(transcript.get("source") or "chat")
    external_id = str(transcript.get("external_id") or f"{source}-{int(datetime.now().timestamp())}")
    session_id = str(transcript.get("session_id") or external_id)
    messages = _normalize_messages(transcript)
    if not messages:
        raise ValueError("Keine importierbaren Nachrichten im Transcript")

    pid = project_id or DEFAULT_PROJECT
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    inbox_dir = INBOX_ROOT / "chats" / day
    inbox_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{source}-{_slug(external_id, 32)}.md"
    inbox_path = inbox_dir / fname
    inbox_path.write_text(_render_markdown(transcript, messages), encoding="utf-8")

    chunk_ids = _upsert_chunks(
        source=source,
        chat_id=session_id,
        messages=messages,
        source_path=str(inbox_path),
        project_id=pid,
    )

    preview = messages[0]["text"][:200] if messages else ""
    audit_hash = write_llm_audit(
        tenant_id,
        model=f"chat-import/{source}",
        produced_by=f"chat-import:{source}",
        session_id=session_id,
        prompt_preview=preview,
        response_preview=f"{len(messages)} messages → {inbox_path.name}",
        usage={"message_count": len(messages), "chunk_count": len(chunk_ids)},
    )

    letta_written = 0
    if letta_available():
        for idx, msg in enumerate(messages):
            if msg["role"] != "user":
                continue
            answer = ""
            if idx + 1 < len(messages) and messages[idx + 1]["role"] == "assistant":
                answer = messages[idx + 1]["text"]
            episode = format_archival_episode(msg["text"], source, answer)
            result = insert_archival(tenant_id, episode)
            if result.get("success"):
                letta_written += 1

    return {
        "ok": True,
        "source": source,
        "external_id": external_id,
        "session_id": session_id,
        "path": str(inbox_path),
        "message_count": len(messages),
        "chunk_count": len(chunk_ids),
        "chunk_ids": chunk_ids,
        "letta_episodes": letta_written,
        "audit_hash": audit_hash,
        "tenant_id": tenant_id,
    }
