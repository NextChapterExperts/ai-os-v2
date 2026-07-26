"""FastAPI Contract & Endpoint Security Tests for Orchestrator."""

from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.server import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "orchestrator"}


def test_dispatch_ping_intent():
    payload = {
        "intent": "ping",
        "tenant_id": "nextchapter",
        "params": {},
    }
    res = client.post("/v1/dispatch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["intent"] == "ping"
    assert data["result"]["answer"] == "pong"
    assert "run_id" in data


def test_list_brain_offerings():
    res = client.get("/v1/brain/offerings")
    assert res.status_code == 200
    assert "offerings" in res.json()


def test_list_brain_engagements():
    res = client.get("/v1/brain/engagements")
    assert res.status_code == 200
    assert "engagements" in res.json()


def test_capture_stats_endpoint():
    res = client.get("/v1/capture/stats")
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert "inbox_path" in data


def test_compute_mode_endpoint():
    res = client.get("/v1/compute/mode")
    assert res.status_code == 200
    data = res.json()
    assert "active_mode" in data or "modes" in data


def test_models_endpoint():
    res = client.get("/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
