"""Native MCP-Adapter für Google-Zugriff (mail, calendar, drive, meetings)."""

from core.mcp_gateway.adapters import calendar, drive, mail, meetings  # noqa: F401

__all__ = ["calendar", "drive", "mail", "meetings"]
