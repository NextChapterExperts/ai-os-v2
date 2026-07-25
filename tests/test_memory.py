"""Memory- und Query-Router Contract-Tests."""

from __future__ import annotations

import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.memory_store import resolve_window  # noqa: E402
from core.orchestrator.query_router import route_query  # noqa: E402


def test_policy_query_no_l1_no_letta():
    plan = route_query("Welche Decision gilt für consulting?")
    assert plan.use_g is True
    assert plan.use_l1 is False
    assert plan.use_letta is False


def test_temporal_query_uses_letta():
    plan = route_query("Was haben wir gestern besprochen?")
    assert plan.use_letta is True
    assert plan.use_l1 is False


def test_resolve_window_yesterday():
    _start, _end, mode = resolve_window("Was haben wir gestern gemacht?")
    assert mode == "yesterday"


@pytest.mark.integration
def test_letta_roundtrip_if_available():
    from core.memory_gateway.letta_client import insert_episode, is_available, search_archival

    if not is_available():
        pytest.skip("Letta nicht erreichbar")

    marker = "TEST-ROUNDTRIP-MEMORY-GATE-2026"
    insert_episode("nextchapter", marker, "test", "Antwort kurz")
    rows = list_archival("nextchapter", max_items=500)
    assert any(marker in r.get("text", "") for r in rows)
