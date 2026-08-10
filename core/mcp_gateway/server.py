"""MCP Gateway — Allowlist + native Google-Adapter (mail, calendar, drive)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Adapter registrieren (Side-Effect)
import core.mcp_gateway.adapters  # noqa: F401

from core.mcp_gateway.adapters.registry import allowlist, dispatch

app = FastAPI(title="AI-OS MCP Gateway", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPCallRequest(BaseModel):
    server: str = Field(..., alias="server_id")
    tool: str = Field(..., alias="tool_name")
    arguments: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "nextchapter"

    model_config = {"populate_by_name": True}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-gateway"}


@app.get("/v1/servers")
async def list_servers() -> dict[str, Any]:
    registered = allowlist()
    servers = []
    for server_id, tools in registered.items():
        from core.google import auth as google_auth

        status = "connected" if google_auth.secrets_configured() else "stub"
        if server_id not in ("mail", "calendar", "drive", "meetings"):
            status = "stub"
        servers.append({"id": server_id, "status": status, "tools": tools})
    return {"servers": servers}


@app.post("/v1/call")
async def call_tool(req: MCPCallRequest) -> dict[str, Any]:
    registered = allowlist()
    allowed = registered.get(req.server)
    if not allowed:
        raise HTTPException(404, f"MCP server not allowlisted: {req.server}")
    if req.tool not in allowed:
        raise HTTPException(403, f"Tool not allowlisted: {req.server}.{req.tool}")

    args = dict(req.arguments)
    args.setdefault("tenant_id", req.tenant_id)
    result = dispatch(req.server, req.tool, args)
    if not result.get("ok"):
        code = 501 if result.get("error") == "unknown_tool" else 502
        raise HTTPException(code, result.get("message") or result.get("error"))

    return {
        "status": "ok",
        "server": req.server,
        "tool": req.tool,
        "result": result,
        "audit": {"tenant_id": req.tenant_id, "via": "mcp-gateway"},
    }
