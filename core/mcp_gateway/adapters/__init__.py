"""Native MCP-Adapter für Google-Zugriff (mail, calendar, drive)."""

from core.mcp_gateway.adapters import calendar, drive, mail  # noqa: F401

__all__ = ["calendar", "drive", "mail"]
