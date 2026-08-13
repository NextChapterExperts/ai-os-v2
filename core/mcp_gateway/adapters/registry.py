"""MCP-Adapter-Registry — native Handler für mail, calendar, drive."""

from __future__ import annotations

from typing import Any, Callable

Handler = Callable[[dict[str, Any]], dict[str, Any]]

_HANDLERS: dict[str, dict[str, Handler]] = {}


def register(server_id: str, tool_name: str):
    def deco(fn: Handler) -> Handler:
        _HANDLERS.setdefault(server_id, {})[tool_name] = fn
        return fn

    return deco


def list_registered_tools() -> dict[str, list[str]]:
    return {sid: sorted(tools.keys()) for sid, tools in _HANDLERS.items()}


def dispatch(server_id: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tools = _HANDLERS.get(server_id) or {}
    handler = tools.get(tool_name)
    if not handler:
        # Dynamische Auflösung für beliebige Docker MCP Catalog Server (z. B. docker_jira, docker_stripe, docker_sentry)
        if server_id.startswith("docker_") or server_id.startswith("mcp_docker_"):
            from core.mcp_gateway.adapters.docker_adapter import DockerMCPAdapter
            adapter = DockerMCPAdapter(server_id)
            return adapter.execute_tool(tool_name, arguments or {})

        return {
            "ok": False,
            "error": "unknown_tool",
            "message": f"Tool {server_id}.{tool_name} nicht registriert",
        }

    try:
        result = handler(arguments or {})
        if "ok" not in result:
            result["ok"] = True
        return result
    except Exception as exc:
        return {"ok": False, "error": "adapter_failed", "message": str(exc)}


def allowlist() -> dict[str, list[str]]:
    return list_registered_tools()
