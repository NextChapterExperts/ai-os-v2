"""Unit tests for Context Bundle Resolution (6 Slices)."""

from __future__ import annotations

import os
import sys
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.context_resolution import resolve_context, resolve_context_async


def test_resolve_context_sync_structure():
    bundle = resolve_context("memory_ask", "nextchapter", {"query": "Policy"})
    assert "system" in bundle
    assert "domain" in bundle
    assert "task" in bundle
    assert "retrieval" in bundle
    assert "episodic" in bundle
    assert "guardrail" in bundle
    assert "skill" in bundle
    assert bundle["system"]["tenant"] == "nextchapter"


@pytest.mark.asyncio
async def test_resolve_context_async_performance():
    bundle = await resolve_context_async("memory_ask", "nextchapter", {"query": "Datenschutz"})
    assert "system" in bundle
    assert "resolution_time_ms" in bundle["system"]
    assert bundle["system"]["resolution_time_ms"] < 500  # Fast execution
    assert bundle["task"]["intent"] == "memory_ask"
