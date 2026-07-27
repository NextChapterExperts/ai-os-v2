"""Regression test suite for Compute Mode fallback, all 4 modes completeness, and service health."""

from __future__ import annotations

import os
import sys
import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.orchestrator.server import app
from core.memory_gateway.config import (
    compute_mode_snapshot,
    set_active_mode,
    list_compute_modes,
)

client = TestClient(app)


def test_all_four_compute_modes_present_in_registry():
    """Verifiziert, dass alle 4 Compute-Modi (sovereign, balanced, premium, coding) in der Memory-Gateway Config vorhanden sind."""
    snapshot = compute_mode_snapshot()
    modes = snapshot.get("modes", [])
    mode_ids = {m["id"] for m in modes if isinstance(m, dict)}
    expected = {"sovereign", "balanced", "premium", "coding"}
    assert expected.issubset(mode_ids), f"Fehlende Modi in Registry: {expected - mode_ids}"
    assert len(modes) >= 4


def test_compute_mode_switcher_full_cycle():
    """Testet das Umschalten durch alle 4 Modi und Zurücksetzen auf sovereign."""
    for mode in ["sovereign", "balanced", "premium", "coding"]:
        set_active_mode(mode)
        current = compute_mode_snapshot()
        assert current["active_mode"] == mode

    # Restore sovereign
    set_active_mode("sovereign")
    assert compute_mode_snapshot()["active_mode"] == "sovereign"


def test_orchestrator_health_and_models_endpoints():
    """Verifiziert die HTTP API-Endpunkte /health, /v1/models und /v1/compute/mode."""
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json().get("status") == "ok"

    models_res = client.get("/v1/models")
    assert models_res.status_code == 200
    data = models_res.json()
    assert "modes" in data
    mode_ids = {m["id"] for m in data.get("modes", [])}
    assert {"sovereign", "balanced", "premium", "coding"}.issubset(mode_ids)

    compute_res = client.get("/v1/compute/mode")
    assert compute_res.status_code == 200
    compute_data = compute_res.json()
    compute_mode_ids = {m["id"] for m in compute_data.get("modes", [])}
    assert {"sovereign", "balanced", "premium", "coding"}.issubset(compute_mode_ids)
