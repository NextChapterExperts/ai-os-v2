"""Memory ask — episodisch (Letta/SQLite) + bei Projektstand federiert (Graph/L1)."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.memory_gateway.client import chat_completion
from core.memory_gateway.config import OLLAMA_MODEL
from core.memory_gateway.episodic_search import context_chunks

from ..memory_store import DEFAULT_PROJECT, resolve_window

REPO_ROOT = Path(__file__).resolve().parents[3]
ACTIVE_ROOT = Path(os.environ.get("AIOS_ACTIVE_ROOT", REPO_ROOT.parent / "active"))

# Projektstand / Roadmap — braucht kuratiertes Wissen (ROADMAP, Graph), nicht nur Chat-Episoden.
_FEDERATED_KEYWORDS = (
    "stand im",
    "stand des",
    "stand bei",
    "stand von",
    "stand in",
    "wie ist der stand",
    "wie ist stand",
    "projektstand",
    "projekt stand",
    "fortschritt",
    "meilenstein",
    "status im",
    "status des",
    "status bei",
    "status von",
    "1100-ai-os",
    "ai-os-v2",
    "ai os v2",
    "wie weit",
    "implementierungsstand",
    "ist-stand",
    "roadmap",
    "phasenfortschritt",
    "haben wir",
    "berücksichtigt",
    "schon mal",
    "im projekt",
)

_PROJECT_SLUG_RE = re.compile(r"1100[- ]?ai[- ]?os[- ]?v2|ai-os-v2", re.I)


@lru_cache(maxsize=1)
def _active_project_tokens() -> tuple[str, ...]:
    """Slugs und Namensfragmente aus Projekte/active/."""
    tokens: set[str] = set()
    if not ACTIVE_ROOT.is_dir():
        return tuple()
    for d in ACTIVE_ROOT.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        slug = d.name.lower()
        tokens.add(slug)
        tokens.add(slug.replace("-", " "))
        for part in slug.split("-"):
            if len(part) >= 4:
                tokens.add(part)
    return tuple(sorted(tokens, key=len, reverse=True))


def _mentions_active_project(question: str) -> bool:
    lower = question.lower()
    return any(tok in lower for tok in _active_project_tokens())


def _needs_federated_context(question: str) -> bool:
    lower = question.lower()
    if _PROJECT_SLUG_RE.search(question):
        return True
    if _mentions_active_project(question):
        return True
    if any(k in lower for k in _FEDERATED_KEYWORDS):
        return True
    if "stand" in lower and any(w in lower for w in ("projekt", "bei", "von", "in")):
        return True
    return False


def _enhance_federated_query(question: str) -> str:
    """Suchanfrage für Graph + L1 Qdrant anreichern."""
    base = question.strip()
    lower = base.lower()
    extras: list[str] = []
    if _PROJECT_SLUG_RE.search(base) or "ai-os" in lower:
        extras.extend(["AI-OS v2", "ROADMAP", "Phase", "Memory"])
    elif _mentions_active_project(base):
        extras.extend(["ROADMAP", "Engagement", "org:KnowledgeAsset"])
    if any(k in lower for k in ("stand", "status", "fortschritt")):
        extras.append("Implementierungsstand")
    if not extras:
        return base
    return f"{base} {' '.join(dict.fromkeys(extras))}"


async def _federated_hits(
    question: str,
    tenant_id: str,
    *,
    limit: int = 14,
) -> list[dict[str, Any]]:
    """Graph + L1 Qdrant + episodisch via Unified Search."""
    from .unified_search import run as unified_search_run

    query = _enhance_federated_query(question)
    result = await unified_search_run({}, tenant_id, {"query": query, "limit": limit})
    hits = result.get("sources") or []
    # Kuratiert/Graph vor Episoden — ROADMAP ist authoritative für Projektstand
    priority = {"graph": 0, "curated": 1, "raw-file": 2, "episodic": 3}
    hits.sort(key=lambda h: (priority.get(str(h.get("source_type")), 9), -float(h.get("score") or 0)))

    chunks: list[dict[str, Any]] = []
    for h in hits:
        st = str(h.get("source_type") or "search")
        title = str(h.get("title") or "")
        snippet = str(h.get("snippet") or "")
        body = f"[{st}] {title}\n{snippet}"
        chunks.append(
            {
                "id": str(h.get("id") or title[:32]),
                "role": st,
                "title": title,
                "body": body,
                "chat_id": str(h.get("collection") or st),
                "source": st,
                "ingested_at": "",
            }
        )
    return chunks


def _system_prompt(*, federated: bool) -> str:
    system = (
        "Du bist das AI-OS Company Brain. Antworte auf Deutsch, nur aus dem Kontext. "
        "KURZ: max. 5 Bulletpoints, eine Zeile je Punkt, nur große Themen. "
        "Keine Dateipfade. Max. 1 Satz Fazit."
    )
    if federated:
        system += (
            " Bei Projektstand-Fragen: KnowledgeAsset ROADMAP, org:Claim und Graph-Knoten "
            "haben Vorrang vor Chat-Episoden. Nenne konkrete Phasen, erledigte Bausteine (✅) "
            "und offene Punkte (⏳), wenn im Kontext vorhanden."
        )
    return system


def _format_context_for_llm(
    chunks: list[dict[str, Any]],
    *,
    max_chars: int = 5500,
) -> tuple[str, list[dict[str, Any]]]:
    ctx_parts: list[str] = []
    used_chunks: list[dict[str, Any]] = []
    used = 0
    for c in chunks:
        body = str(c.get("body", ""))
        block = f"[{c.get('role', 'user')}] {body[:280]}"
        if used + len(block) > max_chars:
            break
        ctx_parts.append(block)
        used_chunks.append(
            {
                "id": c.get("id"),
                "role": c.get("role"),
                "title": c.get("title"),
                "source": c.get("source"),
                "chat_id": c.get("chat_id"),
                "bodyPreview": body[:500],
                "bodyLength": len(body),
            }
        )
        used += len(block)
    return "\n---\n".join(ctx_parts), used_chunks


def build_llm_context(
    *,
    run_id: str,
    tenant_id: str,
    question: str,
    chunks: list[dict[str, Any]],
    context_text: str,
    chunks_used: list[dict[str, Any]],
    federated: bool,
    federated_query: str | None,
    memory_backend: str,
    model: str,
) -> dict[str, Any]:
    system = _system_prompt(federated=federated)
    user_content = f"Frage: {question}\n\nGedächtnis-Kontext:\n{context_text}"
    return {
        "runId": run_id,
        "tenantId": tenant_id,
        "handler": "memory_ask",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "routing": {
            "intent": "memory_ask",
            "federated": federated,
            "memoryBackend": memory_backend,
            "modelTier": "local",
            "model": model,
        },
        "retrieval": {
            "question": question,
            "federatedQuery": federated_query,
            "chunkCountTotal": len(chunks),
            "chunkCountUsed": len(chunks_used),
            "chunks": chunks_used,
        },
        "prompt": {
            "system": system,
            "user": user_content,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "contextCharCount": len(context_text),
        },
    }


async def _summarize(
    question: str,
    chunks: list[dict[str, Any]],
    tenant_id: str,
    *,
    federated: bool = False,
) -> tuple[str, str, str, list[dict[str, Any]]]:
    if not chunks:
        return "Im Gedächtnis dieses Projekts liegen dazu noch keine Einträge.", "none", "", []

    context_text, chunks_used = _format_context_for_llm(chunks)
    system = _system_prompt(federated=federated)
    user_content = f"Frage: {question}\n\nGedächtnis-Kontext:\n{context_text}"

    result = await chat_completion(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        tenant_id=tenant_id,
        produced_by="memory_ask",
        max_tokens=320,
        temperature=0.2,
        persist=False,
    )
    return (
        result["content"] or "Keine Antwort.",
        result.get("model") or OLLAMA_MODEL,
        context_text,
        chunks_used,
    )


def _merge_chunks(
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    *,
    max_total: int = 24,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for c in primary + secondary:
        key = str(c.get("id") or "") + str(c.get("body", ""))[:80]
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)
        if len(merged) >= max_total:
            break
    return merged


async def run(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    question = str(params.get("query") or params.get("intent_text") or "Was haben wir heute gemacht?")
    project_id = str(params.get("project_id") or DEFAULT_PROJECT)
    run_id = str(params.get("run_id") or "")
    _start, _end, mode = resolve_window(question)

    federated = _needs_federated_context(question)
    federated_query = _enhance_federated_query(question) if federated else None
    episodic_limit = 6 if federated else 20
    episodic_chunks, memory_backend = context_chunks(
        tenant_id, question, project_id=project_id, limit=episodic_limit
    )

    if federated:
        fed_chunks = await _federated_hits(question, tenant_id)
        # Kuratiert/Graph zuerst; episodisch nur ergänzend (weniger Rauschen aus Letta)
        chunks = _merge_chunks(fed_chunks, episodic_chunks if len(fed_chunks) < 8 else [])
        memory_backend = "federated" if fed_chunks else memory_backend
    else:
        chunks = episodic_chunks

    answer, model, context_text, chunks_used = await _summarize(
        question, chunks, tenant_id, federated=federated
    )
    llm_context = build_llm_context(
        run_id=run_id,
        tenant_id=tenant_id,
        question=question,
        chunks=chunks,
        context_text=context_text,
        chunks_used=chunks_used,
        federated=federated,
        federated_query=federated_query,
        memory_backend=memory_backend,
        model=model,
    )
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
        for c in chunks[:10]
    ]
    return {
        "kind": "ask",
        "answer": answer,
        "mode": mode,
        "memoryBackend": memory_backend,
        "federated": federated,
        "detail": False,
        "projectId": project_id,
        "model": model,
        "sources": sources,
        "sourceCount": len(chunks),
        "tenant_id": tenant_id,
        "runId": run_id,
        "llmContext": llm_context,
    }
