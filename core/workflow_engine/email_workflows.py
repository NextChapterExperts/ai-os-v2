"""Email-Agent Workflows — Registry für Fachagenten-Cockpit."""

from __future__ import annotations

from agents.email.agent import EmailAgent
from agents.email.dataproducts import (
    InvoicePipelineReport,
    InvoiceRunUserInput,
)
from sdk.mcp_adapter import MCPAdapter
from sdk.tenant_context import TenantContext

from .generic_runner import register_workflow


async def handle_email_invoices(input_dp: InvoiceRunUserInput) -> InvoicePipelineReport:
    tenant_id = "nextchapter"
    ctx = TenantContext.for_tenant(tenant_id)
    mcp = MCPAdapter(tenant_id=tenant_id, agent_id="email-agent")
    agent = EmailAgent(ctx=ctx, mcp=mcp)
    return await agent.run(input_dp.to_agent_request(tenant_id=tenant_id))


register_workflow(
    workflow_id="email-invoices",
    name="Gmail-Rechnungen extrahieren",
    description=(
        "Scannt Gmail nach Rechnungs-Kandidaten, archiviert PDFs in Google Drive "
        "und schreibt neue Zeilen ins konfigurierte Google Sheet (email-agent via MCP)."
    ),
    input_schema=InvoiceRunUserInput,
    output_schema=InvoicePipelineReport,
    handler=handle_email_invoices,
)
