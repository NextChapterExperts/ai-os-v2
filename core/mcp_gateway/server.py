"""MCP Gateway skeleton — Allowlist + stubs for mail/calendar (P5)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AI-OS MCP Gateway", version="2.0.0-skeleton")

ALLOWLIST = {
    "mail": ["list_open_actions"],
    "calendar": ["list_today"],
}


class MCPCallRequest(BaseModel):
    server: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "nextchapter"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-gateway"}


@app.get("/v1/servers")
async def list_servers() -> dict[str, Any]:
    return {
        "servers": [
            {"id": "mail", "status": "stub", "tools": ALLOWLIST["mail"]},
            {"id": "calendar", "status": "stub", "tools": ALLOWLIST["calendar"]},
        ]
    }


@app.post("/v1/call")
async def call_tool(req: MCPCallRequest) -> dict[str, Any]:
    allowed = ALLOWLIST.get(req.server)
    if not allowed:
        raise HTTPException(404, f"MCP server not allowlisted: {req.server}")
    if req.tool not in allowed:
        raise HTTPException(403, f"Tool not allowlisted: {req.server}.{req.tool}")

    if req.server == "mail" and req.tool == "list_open_actions":
        from core.orchestrator.mcp_clients import mail_stub

        result = await mail_stub.list_open_actions(req.tenant_id)
    elif req.server == "calendar" and req.tool == "list_today":
        from core.orchestrator.mcp_clients import calendar_stub

        result = await calendar_stub.list_today(req.tenant_id)
    else:
        raise HTTPException(501, "Not implemented")

    return {
        "status": "ok",
        "server": req.server,
        "tool": req.tool,
        "result": result,
        "audit": {"tenant_id": req.tenant_id, "via": "mcp-gateway"},
    }
