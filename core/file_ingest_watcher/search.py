#!/usr/bin/env python3
"""Kleines CLI zum Testen der raw-files Suche (Chunking/Embedding-Check).

Nutzung:
    ./run.sh # nicht dafuer - stattdessen:
    .venv/bin/python search.py "meine suchanfrage" [--limit 5] [--project slug]
"""

from __future__ import annotations

import argparse
import os

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "raw-files")
EMBED_MODEL = os.environ.get(
    "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--project", default=None, help="Filter auf project_slug (z.B. active/waqam-doku)")
    args = parser.parse_args()

    embedder = TextEmbedding(model_name=EMBED_MODEL)
    vector = list(embedder.embed([args.query]))[0]

    client = QdrantClient(url=QDRANT_URL)
    query_filter = None
    if args.project:
        query_filter = qm.Filter(
            must=[qm.FieldCondition(key="project_slug", match=qm.MatchValue(value=args.project))]
        )

    hits = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=vector.tolist(),
        limit=args.limit,
        query_filter=query_filter,
        with_payload=True,
    )

    print(f"\nSuche: {args.query!r}  ->  {len(hits)} Treffer\n" + "=" * 70)
    for i, hit in enumerate(hits, 1):
        p = hit.payload
        snippet = (p.get("text") or "").strip().replace("\n", " ")
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        print(f"\n#{i}  score={hit.score:.3f}  {p.get('project_slug')}/{p.get('file_name')}  (Chunk {p.get('chunk_index')}/{p.get('chunk_count')})")
        print(f"    Pfad: {p.get('source_path')}")
        print(f"    Text: {snippet}")
    print()


if __name__ == "__main__":
    main()
