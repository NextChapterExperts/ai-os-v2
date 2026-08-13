"""Native MCP-Adapter für Google-Zugriff (mail, calendar, drive, meetings)."""

from core.mcp_gateway.adapters import calendar, docker_adapter, drive, mail, meetings, web_search  # noqa: F401

__all__ = ["calendar", "drive", "mail", "meetings", "docker_adapter", "web_search"]


