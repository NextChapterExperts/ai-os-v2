#!/usr/bin/env python3
"""L1-Curator manuell oder per Cron (wöchentlich So 03:00) ausführen."""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)


def _main() -> int:
    from core.memory.l1_curator import run_l1_curate

    parser = argparse.ArgumentParser(description="L1-Curator — Qdrant content Dedup + Rolling")
    parser.add_argument(
        "--mode",
        action="append",
        dest="modes",
        choices=["stats", "exact_dedup", "semantic_dedup", "rolling"],
        help="Modus (mehrfach möglich; Default: alle)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_l1_curate(modes=args.modes, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
