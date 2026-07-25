"""Memory ask — SQLite capture + Memory Gateway (eine Tür, P11/P19)."""

from __future__ import annotations

from typing import Any

from core.memory_gateway.client import chat_completion
from core.memory_gateway.config import OLLAMA_MODEL

from ..memory_store import DEFAULT_PROJECT, chunks_in_window, resolve_window


async def _summarize(question: str, chunks: list[dict[str, Any]], tenant_id: str) -> tuple[str, str]:
    if not chunks:
        return "Im Gedächtnis dieses Projekts liegen dazu noch keine Einträge.", "none"

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
    result = await chat_completion(
        [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Frage: {question}\n\nGedächtnis-Kontext:\n{context}",
            },
        ],
        tenant_id=tenant_id,
        produced_by="memory_ask",
        max_tokens=280,
        temperature=0.2,
    )
    return result["content"] or "Keine Antwort.", result.get("model") or OLLAMA_MODEL


async def run(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    question = str(params.get("query") or params.get("intent_text") or "Was haben wir heute gemacht?")
    project_id = str(params.get("project_id") or DEFAULT_PROJECT)
    start, end, mode = resolve_window(question)
    chunks = chunks_in_window(project_id, start, end)
    answer, model = await _summarize(question, chunks, tenant_id)
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
        "mode": mode,
        "detail": False,
        "projectId": project_id,
        "model": model,
        "sources": sources,
        "sourceCount": len(chunks),
        "tenant_id": tenant_id,
    }
