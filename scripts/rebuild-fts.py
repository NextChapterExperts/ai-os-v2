#!/usr/bin/env python3
"""FTS5-Index für memory.db neu aufbauen."""

from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory_gateway.sqlite_schema import rebuild_fts  # noqa: E402


def main() -> int:
    stats = rebuild_fts()
    print(f"FTS rebuild OK: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
