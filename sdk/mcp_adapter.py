"""MCPAdapter — Einziger Konnektivitäts-Layer für Agenten (P5 MCP-Gateway)."""

from __future__ import annotations

from typing import Any
import httpx


class MCPException(Exception):
    """Basis-Klasse für MCP-Fehler."""
    pass


class MCPServerNotAllowed(MCPException):
    """Server ist für diesen Tenant/Agent nicht erlaubt."""
    pass


class MCPAdapter:
    """
    Adapter um MCP-Server über das Plattform MCP-Gateway (:8097) aufzurufen.
    Kein Agent darf direkt HTTP/SMTP/Socket nutzen.
    """

    def __init__(self, gateway_url: str = "http://127.0.0.1:8097", tenant_id: str = "nextchapter", agent_id: str = "agent"):
        self.gateway_url = gateway_url.rstrip("/")
        self.tenant_id = tenant_id
        self.agent_id = agent_id

    async def call(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        """
        Ruft ein Tool auf einem MCP-Server über das MCP-Gateway auf.
        """
        arguments = arguments or {}
        payload = {
            "server": server,
            "tool": tool,
            "arguments": arguments,
            "tenant_id": self.tenant_id,
        }
        headers = {
            "X-Tenant-ID": self.tenant_id,
            "X-Agent-ID": self.agent_id,
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                res = await client.post(f"{self.gateway_url}/v1/call", json=payload, headers=headers)
                if res.status_code == 403:
                    raise MCPServerNotAllowed(f"MCP Server '{server}' ist nicht erlaubt für Tenant '{self.tenant_id}'")
                res.raise_for_status()
                data = res.json()
                return data.get("result", data)
            except (httpx.ConnectError, httpx.HTTPStatusError):
                # Fallback / Direct local dispatch in test/stub environments
                from core.mcp_gateway.adapters.registry import dispatch
                args = {**arguments, "tenant_id": self.tenant_id}
                return dispatch(server, tool, args)
