"""Unified Search — foederiert ueber Company Brain (content) und raw-files.

Phase-1-Baustein (siehe ROADMAP.md §6.5). Fragt beide Qdrant-Collections
parallel ab und kennzeichnet jeden Treffer mit `source_type`, damit
kuratiertes Wissen nie mit ungeprueften Rohdateien verwechselt wird
(siehe docs/adr/0002-file-ingest-watcher-und-rolle-von-cursor.md).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

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
            "tenant_id": tenant_id,
        }

    embedder = _get_embedder()
    vector = list(embedder.embed([query]))[0].tolist()
    client = _get_client()

    curated = _search_collection(client, vector, CONTENT_COLLECTION, "curated", limit)
    raw_files = _search_collection(client, vector, RAW_FILES_COLLECTION, "raw-file", limit)

    combined = sorted(curated + raw_files, key=lambda r: r["score"], reverse=True)

    return {
        "kind": "search",
        "query": query,
        "sources": combined,
        "sourceCount": len(combined),
        "curatedCount": len(curated),
        "rawFileCount": len(raw_files),
        "tenant_id": tenant_id,
    }
