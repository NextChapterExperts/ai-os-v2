"""Tests für MCP Google-Adapter (Dry-Run, ohne echte Credentials)."""

from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import core.mcp_gateway.adapters  # noqa: F401 — registriert Handler
from core.mcp_gateway.adapters.registry import allowlist, dispatch


def test_allowlist_contains_google_servers():
    registered = allowlist()
    assert "mail" in registered
    assert "calendar" in registered
    assert "drive" in registered
    assert "get_recent" in registered["mail"]
    assert "get_today" in registered["calendar"]
    assert "poll_chats" in registered["drive"]


def test_mail_get_recent_dry_run():
    result = dispatch("mail", "get_recent", {"dry_run": True})
    assert result["ok"] is True
    assert result.get("dry_run") is True
    assert result["count"] == 0


def test_calendar_get_today_dry_run():
    result = dispatch("calendar", "get_today", {"dry_run": True})
    assert result["ok"] is True
    assert result.get("status") == "dry-run"
    assert "date" in result


def test_drive_poll_chats_dry_run():
    result = dispatch("drive", "poll_chats", {"dry_run": True})
    assert result["ok"] is True
    assert result.get("imported") == 0


def test_drive_list_sources():
    result = dispatch("drive", "list_sources", {})
    assert result["ok"] is True
    assert isinstance(result.get("sources"), list)
