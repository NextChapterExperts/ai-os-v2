"""Unified Search — foederiert ueber Knowledge Graph (G), Company Brain
(content), raw-files und episodisches Gedaechtnis (Letta + SQLite).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from core.memory_gateway.episodic_search import search_episodic

from ..kg_search import search_nodes
from ..query_router import SearchPlan, route_query

log = logging.getLogger("unified_search")

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
EMBED_MODEL = os.environ.get(
    "SEARCH_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
CONTENT_COLLECTION = os.environ.get("QDRANT_COLLECTION_CONTENT", "content")
RAW_FILES_COLLECTION = os.environ.get("QDRANT_COLLECTION_RAW_FILES", "raw-files")
DEFAULT_LIMIT = 8

_embedder: TextEmbedding | None = None
_client: QdrantClient | None = None


def _get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=EMBED_MODEL)
    return _embedder


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
    return _client


def _search_collection(
    client: QdrantClient,
    vector: list[float],
    collection: str,
    source_type: str,
    limit: int,
) -> list[dict[str, Any]]:
    try:
        existing = {c.name for c in client.get_collections().collections}
        if collection not in existing:
            return []
        hits = client.query_points(
            collection_name=collection,
            query=vector,
            limit=limit,
            with_payload=True,
        ).points
    except Exception:
        log.exception("Suche in Collection '%s' fehlgeschlagen", collection)
        return []

    results = []
    for hit in hits:
        payload = hit.payload or {}
        title = payload.get("title") or payload.get("file_name") or payload.get("asset_id") or collection
        snippet = str(payload.get("text") or payload.get("snippet") or "")[:280]
        results.append(
            {
                "id": str(hit.id),
                "score": round(float(hit.score), 4),
                "source_type": source_type,
                "title": title,
                "snippet": snippet,
                "project_slug": payload.get("project_slug"),
                "source_path": payload.get("source_path") or payload.get("path"),
                "collection": collection,
            }
        )
    return results


def _graph_hits(tenant_id: str, query: str, plan: SearchPlan) -> list[dict[str, Any]]:
    nodes = search_nodes(tenant_id, query, limit=plan.max_graph_nodes)
    results = []
    for n in nodes:
        relations = [f"{e['edge_type']} \u2192 {e['external_id']}" for e in n["edges_out"]]
        relations += [f"{e['edge_type']} \u2190 {e['external_id']}" for e in n["edges_in"]]
        results.append(
            {
                "id": n["id"],
                "score": 1.0,
                "source_type": "graph",
                "title": f"{n['node_type']}: {n['title']}",
                "snippet": n["snippet"],
                "project_slug": None,
                "source_path": n["k_path"],
                "collection": "kg",
                "relations": relations[:8],
            }
        )
    return results


def _meeting_hits(tenant_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    try:
        from ..meetings_store import list_meetings
        meetings = list_meetings(tenant_id, q=query, limit=limit)
        results = []
        for m in meetings:
            todos_str = ""
            if m.get("todos"):
                todo_items = []
                for t in m["todos"]:
                    if isinstance(t, dict):
                        todo_items.append(t.get("text") or t.get("task") or "")
                    elif isinstance(t, str):
                        todo_items.append(t)
                if todo_items:
                    todos_str = " | To-Dos: " + "; ".join(todo_items)
            snippet = f"{m.get('summary', '')}{todos_str}".strip()[:280] or f"Meeting am {m.get('held_at', '')}"
            results.append(
                {
                    "id": m["id"],
                    "score": 0.95,
                    "source_type": "meeting",
                    "title": f"Meeting: {m['title']}",
                    "snippet": snippet,
                    "project_slug": None,
                    "source_path": f"meetings/{m['id']}",
                    "collection": "meetings.db",
                }
            )
        return results
    except Exception:
        log.exception("Suche in Meeting Store fehlgeschlagen")
        return []


async def run(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    query = str(params.get("query") or params.get("intent_text") or "").strip()
    limit = int(params.get("limit") or DEFAULT_LIMIT)

    if not query:
        return {
            "kind": "search",
            "query": query,
            "sources": [],
            "sourceCount": 0,
            "curatedCount": 0,
            "rawFileCount": 0,
            "graphCount": 0,
            "episodicCount": 0,
            "meetingCount": 0,
            "plan": None,
            "tenant_id": tenant_id,
        }

    user_id = str(params.get("user_id") or (context_bundle.get("system") or {}).get("user_id") or "default_user")

    plan = route_query(query)

    graph_hits = _graph_hits(tenant_id, query, plan) if plan.use_g else []

    episodic_limit = 10 if plan.use_letta else 5
    if plan.use_g and not plan.use_l1 and not plan.use_letta:
        episodic_limit = 0
    episodic_hits = search_episodic(tenant_id, query, limit=episodic_limit, user_id=user_id) if episodic_limit else []

    meeting_hits = _meeting_hits(tenant_id, query, limit=limit)

    curated: list[dict[str, Any]] = []
    raw_files: list[dict[str, Any]] = []
    if plan.use_l1:
        embedder = _get_embedder()
        vector = list(embedder.embed([query]))[0].tolist()
        client = _get_client()
        l1_limit = min(limit, plan.max_l1) or limit
        curated = _search_collection(client, vector, CONTENT_COLLECTION, "curated", l1_limit)
        raw_files = _search_collection(client, vector, RAW_FILES_COLLECTION, "raw-file", l1_limit)

    combined = sorted(
        graph_hits + curated + raw_files + episodic_hits + meeting_hits, key=lambda r: r["score"], reverse=True
    )

    answer = ""
    if combined:
        from .memory_ask import _summarize
        answer, _, _, _ = await _summarize(query, combined[:12], tenant_id)

    return {
        "kind": "ask" if answer else "search",
        "answer": answer,
        "query": query,
        "sources": combined,
        "sourceCount": len(combined),
        "curatedCount": len(curated),
        "rawFileCount": len(raw_files),
        "graphCount": len(graph_hits),
        "episodicCount": len(episodic_hits),
        "plan": plan.model_dump(),
        "tenant_id": tenant_id,
    }
