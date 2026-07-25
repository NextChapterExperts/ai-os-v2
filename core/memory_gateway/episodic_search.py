"""Einheitliche episodische Suche — Letta L2 + SQLite (FTS/Zeitfenster)."""

from __future__ import annotations

from typing import Any

from core.orchestrator.memory_store import (
    DEFAULT_PROJECT,
    chunks_in_window,
    resolve_window,
    search_chunks,
    search_chunks_fts,
)

from .letta_client import is_available as letta_available, search_archival


def _chunk_hit(c: dict[str, Any], *, score: float, collection: str) -> dict[str, Any]:
    body = str(c.get("body") or "")
    return {
        "id": c["id"],
        "score": score,
        "source_type": "episodic",
        "title": c.get("title") or (body[:80] or "Chat"),
        "snippet": body[:280],
        "body": body,
        "project_slug": c.get("project_id"),
        "source_path": c.get("source_path"),
        "collection": collection,
        "backend": c.get("source", "sqlite"),
        "ingested_at": c.get("ingested_at"),
    }


def _letta_hit(ep: dict[str, Any], *, score: float) -> dict[str, Any]:
    text = str(ep.get("text") or "")
    theme = text.split("THEMA:", 1)[1].split("|", 1)[0].strip() if "THEMA:" in text else text[:80]
    return {
        "id": ep.get("id") or text[:32],
        "score": score,
        "source_type": "episodic",
        "title": theme or "Episodisches Gedächtnis",
        "snippet": text[:280],
        "body": text,
        "project_slug": None,
        "source_path": None,
        "collection": "letta-archival",
        "backend": "letta",
        "ingested_at": ep.get("created_at"),
    }


def _dedupe_key(hit: dict[str, Any]) -> str:
    snippet = str(hit.get("snippet") or "")[:120].lower()
    return f"{hit.get('backend')}:{snippet}"


def search_episodic(
    tenant_id: str,
    query: str,
    *,
    limit: int = 10,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    """Letta + SQLite mergen, deduplizieren, nach Score sortieren."""
    pid = project_id or DEFAULT_PROJECT
    start, end, mode = resolve_window(query)
    merged: dict[str, dict[str, Any]] = {}

    if letta_available():
        for ep in search_archival(tenant_id, query, count=limit, start=start, end=end):
            hit = _letta_hit(ep, score=0.92)
            merged[_dedupe_key(hit)] = hit

    if mode in ("yesterday", "week", "today"):
        sqlite_rows = chunks_in_window(pid, start, end, limit=limit)
    else:
        sqlite_rows = search_chunks_fts(query, project_id=pid, limit=limit)
        if not sqlite_rows:
            sqlite_rows = search_chunks(query, project_id=pid, limit=limit)

    for c in sqlite_rows:
        hit = _chunk_hit(c, score=0.9, collection="memory.db")
        key = _dedupe_key(hit)
        if key not in merged:
            merged[key] = hit

    hits = sorted(merged.values(), key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def context_chunks(
    tenant_id: str,
    question: str,
    *,
    project_id: str | None = None,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Chunks für memory_ask — merged, mit Backend-Hinweis."""
    start, end, mode = resolve_window(question)
    pid = project_id or DEFAULT_PROJECT
    hits = search_episodic(tenant_id, question, limit=limit, project_id=pid)

    chunks: list[dict[str, Any]] = []
    backends: set[str] = set()
    for h in hits:
        backends.add(str(h.get("backend") or "sqlite"))
        chunks.append(
            {
                "id": h["id"],
                "role": "user",
                "title": h.get("title") or "",
                "body": str(h.get("body") or h.get("snippet") or ""),
                "chat_id": h.get("collection") or "",
                "source": h.get("backend") or "sqlite",
                "ingested_at": h.get("ingested_at") or "",
            }
        )

    if not chunks:
        sqlite = chunks_in_window(pid, start, end, limit=limit)
        for c in sqlite:
            chunks.append(dict(c))
        backends.add("sqlite")

    if "letta" in backends and "sqlite" in backends:
        backend = "merged"
    elif "letta" in backends:
        backend = "letta"
    else:
        backend = "sqlite"

    return chunks, backend
