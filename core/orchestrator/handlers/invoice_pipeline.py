"""Dispatch — Rechnungs-Pipeline über email-agent (MCP-only)."""

from __future__ import annotations

from typing import Any

from sdk.mcp_adapter import MCPAdapter
from sdk.tenant_context import TenantContext

try:
    from agents.email.agent import EmailAgent, InvoiceExportAgent
    from agents.email.dataproducts import InvoiceRunRequest, InvoiceExportRequest
except (ImportError, ModuleNotFoundError):
    EmailAgent = None  # type: ignore
    InvoiceExportAgent = None  # type: ignore
    InvoiceRunRequest = None  # type: ignore
    InvoiceExportRequest = None  # type: ignore


async def run_invoice_pipeline(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    del context_bundle
    if EmailAgent is None or InvoiceRunRequest is None:
        return {
            "answer": "Email-Agent Modul ist auf dieser Appliance nicht installiert.",
            "status": "skipped",
        }

    ctx = TenantContext.for_tenant(tenant_id)
    mcp = MCPAdapter(tenant_id=tenant_id, agent_id="email-agent")
    agent = EmailAgent(ctx=ctx, mcp=mcp)
    input_dp = InvoiceRunRequest(
        tenant_id=tenant_id,
        produced_by="email-agent",
        dry_run=bool(params.get("dry_run")),
        skip_archive=bool(params.get("skip_archive")),
    )
    report = await agent.run(input_dp)
    return {
        "answer": report.summary,
        "kind": "invoice_pipeline",
        "report": report.model_dump(mode="json"),
        "sources": [],
        "sourceCount": 0,
    }


async def run_invoice_export(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    del context_bundle
    try:
        from agents.email.agent import InvoiceExportAgent
        from agents.email.dataproducts import InvoiceExportRequest
    except (ImportError, ModuleNotFoundError):
        return {
            "answer": "InvoiceExportAgent Modul ist auf dieser Appliance nicht installiert.",
            "status": "skipped",
        }

    ctx = TenantContext.for_tenant(tenant_id)
    mcp = MCPAdapter(tenant_id=tenant_id, agent_id="email-agent")
    agent = InvoiceExportAgent(ctx=ctx, mcp=mcp)
    input_dp = InvoiceExportRequest(
        tenant_id=tenant_id,
        produced_by="email-agent",
        tax_year=int(params.get("year") or params.get("tax_year") or 2025),
        dest=str(params.get("dest") or ""),
        dry_run=bool(params.get("dry_run")),
    )
    export = await agent.run(input_dp)
    return {
        "answer": export.summary,
        "kind": "invoice_export",
        "export": export.model_dump(mode="json"),
        "sources": [],
        "sourceCount": 0,
    }
