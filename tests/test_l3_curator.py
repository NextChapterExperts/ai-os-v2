"""L3-Curator Tests."""

from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory.l3_curator import _claim_id, _parse_extraction, _is_duplicate


def test_claim_id_stable():
    a = _claim_id("Memory Gateway implementiert")
    b = _claim_id("Memory Gateway implementiert")
    c = _claim_id("Anderes Faktum")
    assert a == b
    assert a != c
    assert a.startswith("claim-")


def test_parse_extraction_json():
    raw = 'Some text {"claims": [{"text": "X", "confidence": 0.8}], "profile_facts": []} end'
    data = _parse_extraction(raw)
    assert len(data["claims"]) == 1
    assert data["claims"][0]["text"] == "X"


def test_dedup_empty():
    assert _is_duplicate("Neuer Fakt", [], 0.95) is False
