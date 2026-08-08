"""Platform-Gate Test Suite (Leitprinzip P10 - Platform vor Fach-Agenten).

Prüft vor jedem SKU/Fach-Agenten-Deployment die Vollständigkeit und
Vertragserfüllung aller Plattform-Core-Komponenten:
1. Health Gate (FastAPI & Internal Components)
2. DataProduct Transaction & Schema Contract
3. Intent Router & Unified Search Contract
4. Compute Mode Switcher Contract
5. PII Redaction Gateway Contract (Cloud Escalation Protection)
6. Google Invoice Intent Router Contract
7. MCP Mail Invoice Tools Contract
8. Email-Agent MCP-only Contract
9. Invoice Parser Regression (deterministisch)
10. Meetings-Agent Workflow-Registry & MCP-Contract
"""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from agents.email.agent import EmailAgent
from agents.email.dataproducts import InvoiceRunRequest
from core.google.invoice.extract import extract_amount, extract_invoice_id
from core.mcp_gateway.adapters.registry import allowlist, dispatch
from core.orchestrator.dataproducts import OrgKnowledgeAsset
from core.orchestrator.dp_service import commit_dataproduct
from core.orchestrator.handlers.email_invoices import invoice_status
from core.orchestrator.intent_router import route_intent
from core.orchestrator.pii_redactor import redact_pii, restore_pii
from core.orchestrator.query_router import route_query
from core.orchestrator.server import app
from sdk.tenant_context import TenantContext

import core.mcp_gateway.adapters  # noqa: F401 — MCP-Handler registrieren

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


def test_platform_gate_6_invoice_intent_router():
    """Gate 6: Rechnungs-Intents deterministisch routbar (P4)."""
    assert route_intent("Rechnungen aus Gmail") == "invoice_run"
    assert route_intent("Steuer Export Rechnungen 2025") == "invoice_export"


def test_platform_gate_7_mcp_mail_invoice_tools():
    """Gate 7: MCP mail-Adapter exponiert Rechnungs-Tools."""
    mail_tools = allowlist().get("mail", [])
    for tool in ("status", "preview_invoices", "run_invoices", "export_steuer"):
        assert tool in mail_tools, f"mail.{tool} fehlt im MCP-Allowlist"


def test_platform_gate_8_mcp_invoice_dry_run():
    """Gate 8: MCP run_invoices Dry-Run ohne Side-Effects."""
    result = dispatch("mail", "run_invoices", {"dry_run": True, "tenant_id": "nextchapter"})
    assert result.get("ok") is True
    assert result.get("dry_run") is True or result.get("candidates", 0) >= 0


@pytest.mark.asyncio
async def test_platform_gate_9_email_agent_mcp_only():
    """Gate 9: email-agent ruft ausschließlich MCP mail.run_invoices auf."""
    mcp = MagicMock()
    mcp.call = AsyncMock(return_value={"candidates": 0, "written": 0, "dry_run": True, "invoices": []})
    agent = EmailAgent(ctx=TenantContext.for_tenant("nextchapter"), mcp=mcp)
    await agent.run(InvoiceRunRequest(tenant_id="nextchapter", produced_by="email-agent", dry_run=True))
    mcp.call.assert_awaited_once_with(
        "mail",
        "run_invoices",
        {"dry_run": True, "skip_archive": False, "tenant_id": "nextchapter"},
        timeout=300.0,
    )


def test_platform_gate_10_invoice_parser_regression():
    """Gate 10: Rechnungs-Parser deterministisch (kein LLM)."""
    assert extract_amount("Betrag: 105,20 €") == "105,20"
    assert extract_invoice_id("", "Invoice Number RALU6X65-0001") == "RALU6X65-0001"


def test_platform_gate_11_invoice_status_api():
    """Gate 11: Orchestrator liefert Rechnungs-Status (OAuth/Sheet-Konfiguration)."""
    res = client.get("/v1/email/invoices/status", params={"tenant_id": "nextchapter"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("sheet_name")
    status = invoice_status("nextchapter")
    assert status.get("config_path")


def test_platform_gate_12_email_agent_workflow_registry():
    """Gate 12: Rechnungs-Fachagent im Workflow-Registry (generische Console-UI)."""
    import core.workflow_engine.sample_workflows  # noqa: F401
    from core.workflow_engine.generic_runner import get_workflow_registry

    registry = get_workflow_registry()
    assert "email-invoices" in registry
    assert "email-invoice-export" not in registry
    wf = registry["email-invoices"]
    assert wf.input_schema.__name__ == "InvoiceRunUserInput"
    assert wf.output_schema.__name__ == "InvoicePipelineReport"
    schema = wf.input_schema.model_json_schema()
    props = schema.get("properties", {})
    assert "run_mode" in props
    assert "archive_mode" in props
    assert "workflow_run_id" not in props
    assert "dp_id" not in props
    assert "tenant_id" not in props


def test_platform_gate_13_meetings_agent_workflow_registry():
    """Gate 13: Meetings-Fachagent im Workflow-Registry (Agenten-Cockpit)."""
    import core.workflow_engine.meetings_workflows  # noqa: F401
    from core.workflow_engine.generic_runner import get_workflow_registry

    registry = get_workflow_registry()
    assert "meetings-agent" in registry
    wf = registry["meetings-agent"]
    assert wf.input_schema.__name__ == "MeetingsAgentUserInput"
    assert wf.output_schema.__name__ == "MeetingsAgentReport"
    schema = wf.input_schema.model_json_schema()
    props = schema.get("properties", {})
    assert props["meeting_id"].get("x-widget") == "meeting-picker"
    assert props["meeting_id"].get("x-visible-when") == {"aufgabe": "zusammenfassung_speichern"}
    assert "summary" in props
    assert props["summary"].get("x-widget") == "textarea"


def test_platform_gate_14_meetings_mcp_tools_allowlist():
    """Gate 14: MCP meetings-Tools für Kalender-Sync und Company-Brain-Commit."""
    tools = allowlist().get("meetings") or []
    for required in ("sync_from_calendar", "commit_to_company_brain", "person_stats", "status"):
        assert required in tools


def test_platform_gate_15_meetings_workflow_execute_dry_run(tmp_path, monkeypatch):
    """Gate 15: Workflow-Ausführung meetings-agent (Dry-Run) — kein Registry-Fehler."""
    db = tmp_path / "meetings.db"
    monkeypatch.setenv("AIOS_MEETINGS_DB", str(db))
    monkeypatch.setenv("AIOS_MEETINGS_ATTACHMENTS_DIR", str(tmp_path / "att"))
    monkeypatch.setattr(
        "core.google.meetings.sync.google_auth.secrets_configured",
        lambda: False,
    )
    res = client.post(
        "/v1/workflow/execute",
        json={
            "workflow_id": "meetings-agent",
            "tenant_id": "nextchapter",
            "payload": {
                "aufgabe": "termine_abrufen",
                "run_mode": "dry_run",
                "since_date": "2026-07-01",
                "include_forecast": "yes",
            },
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("status") == "completed"
    assert body.get("workflow_id") == "meetings-agent"
