"""Tests für email-agent Contract (MCP-only, Dry-Run)."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from agents.email.agent import EmailAgent, InvoiceExportAgent
from agents.email.dataproducts import InvoiceExportRequest, InvoiceRunRequest
from sdk.tenant_context import TenantContext


@pytest.mark.asyncio
async def test_email_agent_run_dry_run_via_mcp():
    mcp = MagicMock()
    mcp.call = AsyncMock(
        return_value={
            "candidates": 2,
            "written": 1,
            "dry_run": True,
            "invoices": [{"vendor": "Test GmbH", "amount": "99,00", "invoice_id": "INV-1"}],
            "sheet_url": "",
        }
    )
    agent = EmailAgent(ctx=TenantContext.for_tenant("nextchapter"), mcp=mcp)
    report = await agent.run(
        InvoiceRunRequest(tenant_id="nextchapter", produced_by="email-agent", dry_run=True)
    )
    mcp.call.assert_awaited_once_with(
        "mail",
        "run_invoices",
        {"dry_run": True, "skip_archive": False, "tenant_id": "nextchapter"},
        timeout=300.0,
    )
    assert report.candidates == 2
    assert len(report.invoices) == 1
    assert report.invoices[0].vendor == "Test GmbH"


@pytest.mark.asyncio
async def test_invoice_export_agent_via_mcp():
    mcp = MagicMock()
    mcp.call = AsyncMock(
        return_value={
            "exported": 3,
            "messages": 5,
            "dest": "/tmp/steuer",
            "vendors": ["Acme"],
            "files": ["/tmp/steuer/acme.pdf"],
            "dry_run": True,
        }
    )
    agent = InvoiceExportAgent(ctx=TenantContext.for_tenant("nextchapter"), mcp=mcp)
    export = await agent.run(
        InvoiceExportRequest(tenant_id="nextchapter", produced_by="email-agent", tax_year=2025, dry_run=True)
    )
    mcp.call.assert_awaited_once()
    assert export.exported == 3
    assert export.tax_year == 2025
