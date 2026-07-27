"""Platform-Gate Test Suite (Leitprinzip P10 - Platform vor Fach-Agenten).

Prüft vor jedem SKU/Fach-Agenten-Deployment die Vollständigkeit und
Vertragserfüllung aller Plattform-Core-Komponenten:
1. Health Gate (FastAPI & Internal Components)
2. DataProduct Transaction & Schema Contract
3. Intent Router & Unified Search Contract
4. Compute Mode Switcher Contract
5. PII Redaction Gateway Contract (Cloud Escalation Protection)
"""

from __future__ import annotations

import os
import sys
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.dataproducts import OrgKnowledgeAsset
from core.orchestrator.dp_service import commit_dataproduct
from core.orchestrator.pii_redactor import redact_pii, restore_pii
from core.orchestrator.query_router import route_query
from core.orchestrator.server import app

client = TestClient(app)


def test_platform_gate_1_service_health():
    """Gate 1: Orchestrator Service-Erreichbarkeit und Basiskontrakt."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_platform_gate_2_dataproduct_contract():
    """Gate 2: DataProduct Commit Transaktions- und Schemakontrakt (P15)."""
    asset = OrgKnowledgeAsset(
        tenant_id="nextchapter",
        produced_by="platform-gate-test",
        asset_id="asset:gate-check",
        title="Platform-Gate Test Asset",
        path="README.md",
        kind="document",
        published=True,
    )
    commit_res = commit_dataproduct(asset, dry_run=True)
    assert commit_res["dry_run"] is True
    assert commit_res["node_type"] == "org:KnowledgeAsset"
    assert commit_res["external_id"] == "asset:gate-check"
    assert commit_res["ingest_queued"] is True


def test_platform_gate_3_intent_router_contract():
    """Gate 3: Deterministischer Query Router Kontrakt (P4)."""
    plan_policy = route_query("Welche Policy gilt für IT-Sicherheit?")
    assert plan_policy.use_g is True

    plan_temporal = route_query("Was haben wir gestern besprochen?")
    assert plan_temporal.use_letta is True


def test_platform_gate_4_compute_mode_contract():
    """Gate 4: Compute Mode Switcher Kontrakt (P12 FinOps)."""
    res = client.get("/v1/compute/mode")
    assert res.status_code == 200
    data = res.json()
    assert "active_mode" in data
    assert "modes" in data
    mode_ids = {m.get("id") for m in data.get("modes", [])}
    expected_modes = {"sovereign", "balanced", "premium", "coding"}
    assert expected_modes.issubset(mode_ids), f"Missing compute modes: {expected_modes - mode_ids}"

    # Test mode switching for all modes
    for mode in ["balanced", "premium", "coding", "sovereign"]:
        switch_res = client.post("/v1/compute/mode", json={"mode": mode})
        assert switch_res.status_code == 200
        assert switch_res.json().get("active_mode") == mode


def test_platform_gate_5_pii_redaction_contract():
    """Gate 5: Redaction-Gateway für Cloud-Escalation (P12/P15 DSGVO-Schutz)."""
    sensitive_prompt = "Bitte sende Dokument an peter@example.com und rufen Sie +49 170 123456 an."
    redacted_res = redact_pii(sensitive_prompt)
    assert "[EMAIL_1]" in redacted_res.redacted_text
    assert "peter@example.com" not in redacted_res.redacted_text
    assert redacted_res.pii_count >= 2

    restored = restore_pii(redacted_res.redacted_text, redacted_res.mappings)
    assert restored == sensitive_prompt
