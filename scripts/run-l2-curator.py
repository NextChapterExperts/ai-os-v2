#!/usr/bin/env python3
"""L2-Curator manuell oder per Cron (täglich 02:00) ausführen."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)


async def _main() -> int:
    from core.memory.l2_curator import run_l2_curate

    parser = argparse.ArgumentParser(description="L2-Curator — Tagesdigest → Letta")
    parser.add_argument("--tenant", default=os.environ.get("DEFAULT_TENANT", "nextchapter"))
    parser.add_argument("--day-offset", type=int, default=None, help="0=heute, -1=gestern")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    result = await run_l2_curate(
        args.tenant,
        day_offset=args.day_offset,
        dry_run=args.dry_run,
        force=args.force,
    )
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
