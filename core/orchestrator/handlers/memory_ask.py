"""Memory ask — SQLite capture + Ollama (same path as Console fallback)."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx


MEMORY_DB = os.environ.get("AIOS_MEMORY_DB", "/opt/ai-os/memory/memory.db")
DEFAULT_PROJECT = os.environ.get(
    "AIOS_MEMORY_PROJECT",
    "home-peter-Projekte-1100-AI-OS-V2",
)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "192.168.178.64")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "qwen3.6-64k:latest")


def _berlin_day_bounds() -> tuple[str, str, str]:
    tz = ZoneInfo("Europe/Berlin")
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return (
        start.astimezone(timezone.utc).isoformat(),
        end.astimezone(timezone.utc).isoformat(),
        start.date().isoformat(),
    )


def _chunks_today(project_id: str, limit: int = 40) -> list[dict[str, Any]]:
    if not os.path.exists(MEMORY_DB):
        return []
    start, end, _ = _berlin_day_bounds()
    con = sqlite3.connect(MEMORY_DB)
    con.row_factory = sqlite3.Row
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(chunks)")}
        if "project_id" in cols:
            rows = con.execute(
                """
                SELECT id, role, title, body, chat_id, source, ingested_at, project_id
                FROM chunks
                WHERE project_id = ? AND ingested_at >= ? AND ingested_at < ?
                  AND role = 'user'
                ORDER BY ingested_at ASC
                LIMIT ?
                """,
                (project_id, start, end, limit),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT id, role, title, body, chat_id, source, ingested_at
                FROM chunks
                WHERE ingested_at >= ? AND ingested_at < ? AND role = 'user'
                ORDER BY ingested_at ASC
                LIMIT ?
                """,
                (start, end, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


async def _summarize(question: str, chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "Im Gedächtnis dieses Projekts liegen dazu noch keine Einträge."

    ctx_parts = []
    used = 0
    for c in chunks:
        block = f"[user] {str(c.get('body', ''))[:220]}"
        if used + len(block) > 4500:
            break
        ctx_parts.append(block)
        used += len(block)
    context = "\n---\n".join(ctx_parts)

    system = (
        "Du bist das AI-OS Company Brain. Antworte auf Deutsch, nur aus dem Kontext. "
        "KURZ: max. 5 Bulletpoints, eine Zeile je Punkt, nur große Themen. "
        "Keine Dateipfade. Max. 1 Satz Fazit."
    )
    url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/chat"
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            url,
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "think": False,
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": f"Frage: {question}\n\nGedächtnis-Kontext:\n{context}",
                    },
                ],
                "options": {"temperature": 0.2, "num_predict": 280},
            },
        )
        res.raise_for_status()
        data = res.json()
        msg = data.get("message") or {}
        return (msg.get("content") or msg.get("thinking") or "Keine Antwort.").strip()


async def run(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    question = str(params.get("query") or params.get("intent_text") or "Was haben wir heute gemacht?")
    project_id = str(params.get("project_id") or DEFAULT_PROJECT)
    chunks = _chunks_today(project_id)
    answer = await _summarize(question, chunks)
    sources = [
        {
            "id": c["id"],
            "role": c.get("role", "user"),
            "title": (c.get("title") or str(c.get("body", ""))[:80]),
            "snippet": str(c.get("body", ""))[:120] + "…",
            "chat_id": c.get("chat_id", ""),
            "source": c.get("source", "cursor"),
            "ingested_at": c.get("ingested_at", ""),
        }
        for c in chunks[:8]
    ]
    return {
        "kind": "ask",
        "answer": answer,
        "mode": "today",
        "detail": False,
        "projectId": project_id,
        "model": OLLAMA_MODEL,
        "sources": sources,
        "sourceCount": len(chunks),
        "tenant_id": tenant_id,
    }
