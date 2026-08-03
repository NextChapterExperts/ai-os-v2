"""Regression tests — Google Rechnungs-Pipeline (MCP, Agent, Parser)."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import core.mcp_gateway.adapters  # noqa: F401
from agents.email.agent import EmailAgent
from agents.email.dataproducts import InvoiceRunRequest
from core.google.invoice.extract import extract_amount, is_invoice_candidate
from core.mcp_gateway.adapters.registry import allowlist, dispatch
from core.orchestrator.handlers.email_invoices import invoice_status
from core.orchestrator.intent_router import route_intent
from sdk.tenant_context import TenantContext


def test_intent_router_invoice_run():
    assert route_intent("Rechnungen aus Gmail verarbeiten") == "invoice_run"
    assert route_intent("invoice pipeline") == "invoice_run"


def test_intent_router_invoice_export():
    assert route_intent("Steuer export PDF 2025") == "invoice_export"
    assert route_intent("Rechnungen Steuer-Export") == "invoice_export"


def test_mcp_mail_invoice_tools_registered():
    tools = allowlist().get("mail", [])
    for name in ("preview_invoices", "run_invoices", "export_steuer", "status"):
        assert name in tools


def test_mcp_preview_invoices_dry_stub():
    result = dispatch("mail", "preview_invoices", {"dry_run": True})
    assert result["ok"] is True
    assert result.get("count") == 0


def test_mcp_run_invoices_dry_stub():
    result = dispatch("mail", "run_invoices", {"dry_run": True})
    assert result["ok"] is True
    assert result.get("dry_run") is True


def test_invoice_status_structure():
    status = invoice_status("nextchapter")
    assert "google" in status
    assert "sheet_name" in status
    assert "config_path" in status


def test_invoice_parse_amount_strict():
    assert extract_amount("haben insgesamt 1.252 Themenvorschläge", strict=True) == ""


def test_invoice_candidate_rejects_newsletter():
    assert is_invoice_candidate("Newsletter", "news@example.com", "digest payment", None) is False


@pytest.mark.asyncio
async def test_email_agent_uses_mcp_run_invoices():
    mcp = MagicMock()
    mcp.call = AsyncMock(
        return_value={
            "candidates": 1,
            "written": 1,
            "dry_run": True,
            "invoices": [{"vendor": "Acme", "amount": "10,00", "invoice_id": "X1"}],
        }
    )
    agent = EmailAgent(ctx=TenantContext.for_tenant("nextchapter"), mcp=mcp)
    report = await agent.run(
        InvoiceRunRequest(tenant_id="nextchapter", produced_by="email-agent", dry_run=True)
    )
    mcp.call.assert_awaited_once()
    call_args = mcp.call.await_args
    assert call_args.args[0] == "mail"
    assert call_args.args[1] == "run_invoices"
    assert report.candidates == 1


def test_orchestrator_invoice_status_endpoint():
    from fastapi.testclient import TestClient

    from core.orchestrator.server import app

    client = TestClient(app)
    res = client.get("/v1/email/invoices/status", params={"tenant_id": "nextchapter"})
    assert res.status_code == 200
    data = res.json()
    assert "google" in data
    assert "sheet_name" in data


def test_orchestrator_invoice_run_dry_via_handler():
    """Pipeline Dry-Run über Handler — Agent gegen MCP gemockt."""
    from unittest.mock import patch

    from agents.email.dataproducts import InvoicePipelineReport
    from core.orchestrator.handlers import invoice_pipeline

    fake_report = InvoicePipelineReport(
        tenant_id="nextchapter",
        produced_by="email-agent",
        candidates=2,
        written=2,
        dry_run=True,
        summary="test",
    )

    with patch("core.orchestrator.handlers.invoice_pipeline.EmailAgent") as mock_cls:
        mock_cls.return_value.run = AsyncMock(return_value=fake_report)
        import asyncio

        result = asyncio.run(
            invoice_pipeline.run_invoice_pipeline({}, "nextchapter", {"dry_run": True})
        )
    assert result.get("kind") == "invoice_pipeline"
    assert result.get("report", {}).get("candidates") == 2
