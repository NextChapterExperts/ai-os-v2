#!/usr/bin/env python3
"""Backfill: alle SQLite-Chunks nach Letta L2 Archival synchronisieren."""

from __future__ import annotations

import argparse
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory_gateway.letta_sync import sync_sqlite_to_letta  # noqa: E402
from core.memory_gateway.sqlite_schema import rebuild_fts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="SQLite → Letta Backfill")
    parser.add_argument("--tenant", default=os.environ.get("DEFAULT_TENANT", "nextchapter"))
    parser.add_argument("--source", default=None, help="z.B. cursor, memory-gateway")
    parser.add_argument("--since", default=None, help="ISO timestamp")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Sync-State ignorieren")
    parser.add_argument("--rebuild-fts", action="store_true", help="FTS vor Sync neu bauen")
    args = parser.parse_args()

    if args.rebuild_fts:
        stats = rebuild_fts()
        print(f"[fts] rebuild: {stats}")

    result = sync_sqlite_to_letta(
        args.tenant,
        since=args.since,
        source=args.source,
        limit=args.limit,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
