#!/usr/bin/env python3
"""L3-Curator manuell oder per Cron ausführen."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)


async def _main() -> int:
    from core.memory.l3_curator import run_l3_curate

    parser = argparse.ArgumentParser(description="L3-Curator — L2 → org:Claim + Core")
    parser.add_argument("--tenant", default=os.environ.get("DEFAULT_TENANT", "nextchapter"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Episoden erneut verarbeiten")
    args = parser.parse_args()

    result = await run_l3_curate(args.tenant, dry_run=args.dry_run, force=args.force)
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
