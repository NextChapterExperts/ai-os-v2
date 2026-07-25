"""Unified Search — foederiert ueber Knowledge Graph (G), Company Brain
(content) und raw-files.

Phase-1-Baustein (siehe ROADMAP.md §6.5), seit dem Query-Router-Ausbau
(09-COMPANY-BRAIN.md §12.1) kein reiner Vektor-Fan-out mehr: `query_router`
entscheidet PRO FRAGE deterministisch, ob der Graph, Qdrant oder beides
befragt wird. Jeder Treffer traegt `source_type`, damit Graph-Wahrheit,
kuratiertes Wissen und ungeprueft Rohdateien nie verwechselt werden
(siehe docs/adr/0002-file-ingest-watcher-und-rolle-von-cursor.md).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from ..kg_search import search_nodes
from core.memory_gateway.letta_client import is_available as letta_available, search_archival

from ..memory_store import DEFAULT_PROJECT, chunks_in_window, resolve_window, search_chunks
from ..query_router import SearchPlan, route_query

log = logging.getLogger("unified_search")

# Bewusst NICHT von QDRANT_HOST/QDRANT_PORT aus .env ableiten: die sind
# docker-intern ("qdrant") und vom Host-Prozess (Orchestrator laeuft via
# systemd direkt auf der VM) nicht aufloesbar. Qdrant published seinen Port
# zusaetzlich auf 127.0.0.1:6333 (deploy/infra.yml) - das nutzen wir hier.
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
                # Deterministischer Treffer statt Kosinus-Aehnlichkeit: bewusst
                # vor Vektor-Treffern einsortiert (Geltungsfrage schlaegt "aehnlich").
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


def _sqlite_episodic_hits(query: str) -> list[dict[str, Any]]:
    """SQLite-Fallback, wenn Letta nicht erreichbar ist."""
    start, end, mode = resolve_window(query)
    if mode in ("yesterday", "week"):
        chunks = chunks_in_window(DEFAULT_PROJECT, start, end, limit=10)
    else:
        chunks = search_chunks(query, project_id=DEFAULT_PROJECT, limit=10)
    results = []
    for c in chunks:
        body = str(c.get("body") or "")
        results.append(
            {
                "id": c["id"],
                "score": 0.9,
                "source_type": "episodic",
                "title": c.get("title") or (body[:80] or "Cursor-Chat"),
                "snippet": body[:280],
                "project_slug": c.get("project_id"),
                "source_path": None,
                "collection": "memory.db",
            }
        )
    return results


def _letta_episodic_hits(tenant_id: str, query: str) -> list[dict[str, Any]]:
    start, end, _mode = resolve_window(query)
    episodes = search_archival(tenant_id, query, count=10, start=start, end=end)
    results = []
    for ep in episodes:
        text = str(ep.get("text") or "")
        theme = text.split("THEMA:", 1)[1].split("|", 1)[0].strip() if "THEMA:" in text else text[:80]
        results.append(
            {
                "id": ep.get("id") or text[:32],
                "score": 0.92,
                "source_type": "episodic",
                "title": theme or "Episodisches Gedächtnis",
                "snippet": text[:280],
                "project_slug": None,
                "source_path": None,
                "collection": "letta-archival",
            }
        )
    return results


def _episodic_hits(tenant_id: str, query: str) -> list[dict[str, Any]]:
    """Letta L2 Archival primaer; SQLite-Fallback bei Ausfall."""
    if letta_available():
        hits = _letta_episodic_hits(tenant_id, query)
        if hits:
            return hits
    return _sqlite_episodic_hits(query)


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
            "plan": None,
            "tenant_id": tenant_id,
        }

    plan = route_query(query)

    graph_hits = _graph_hits(tenant_id, query, plan) if plan.use_g else []
    episodic_hits = _episodic_hits(tenant_id, query) if plan.use_letta else []

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
        graph_hits + curated + raw_files + episodic_hits, key=lambda r: r["score"], reverse=True
    )

    return {
        "kind": "search",
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
