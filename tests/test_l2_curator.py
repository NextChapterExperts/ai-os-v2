"""L2-Curator Tests."""

from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory.l2_curator import _day_window, _digest_marker, _build_context


def test_day_window_yesterday_label():
    start, end, label = _day_window(-1)
    assert start < end
    assert len(label) == 10  # YYYY-MM-DD


def test_digest_marker():
    assert _digest_marker("2026-07-24") == "Tagesdigest=2026-07-24"


def test_build_context_truncates():
    chunks = [{"role": "user", "body": "x" * 500} for _ in range(50)]
    ctx = _build_context(chunks, max_chars=1000)
    assert len(ctx) <= 1100
