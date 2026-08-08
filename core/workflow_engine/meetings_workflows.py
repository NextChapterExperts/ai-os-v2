"""Meetings-Fachagent — Registry für Agenten-Cockpit."""

from __future__ import annotations

from agents.meetings.agent import MeetingsAgent
from agents.meetings.dataproducts import MeetingsAgentReport, MeetingsAgentUserInput
from sdk.mcp_adapter import MCPAdapter
from sdk.tenant_context import TenantContext

from .generic_runner import register_workflow


async def handle_meetings_agent(input_dp: MeetingsAgentUserInput) -> MeetingsAgentReport:
    tenant_id = "nextchapter"
    ctx = TenantContext.for_tenant(tenant_id)
    mcp = MCPAdapter(tenant_id=tenant_id, agent_id="meetings-agent")
    agent = MeetingsAgent(ctx=ctx, mcp=mcp)
    return await agent.run(input_dp.to_agent_request(tenant_id=tenant_id))


register_workflow(
    workflow_id="meetings-agent",
    name="Meetings-Agent",
    description=(
        "Lädt Termine aus Google-Kalender (ab 1. Juli 2026) und speichert "
        "Meeting-Zusammenfassungen als org:Meeting im Company Brain."
    ),
    input_schema=MeetingsAgentUserInput,
    output_schema=MeetingsAgentReport,
    handler=handle_meetings_agent,
)
