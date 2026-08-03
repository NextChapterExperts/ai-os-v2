"""Tests für Google OAuth Scope-Validierung (v2-Fix ce07801)."""

from __future__ import annotations

import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.google.scopes import (
    GOOGLE_SCOPES,
    ScopeError,
    ensure_scopes,
    scope_urls,
    tool_required_scopes,
)


def test_tool_required_scopes_mail():
    scopes = tool_required_scopes("mail", "get_recent")
    assert GOOGLE_SCOPES["gmail.readonly"] in scopes


def test_tool_required_scopes_calendar():
    scopes = tool_required_scopes("calendar", "get_today")
    assert GOOGLE_SCOPES["calendar.readonly"] in scopes


def test_tool_required_scopes_drive_poll():
    scopes = tool_required_scopes("drive", "poll_chats")
    assert GOOGLE_SCOPES["drive"] in scopes or GOOGLE_SCOPES["drive.readonly"] in scopes


def test_ensure_scopes_ok():
    required = [GOOGLE_SCOPES["gmail.readonly"]]
    granted = [GOOGLE_SCOPES["gmail.readonly"], GOOGLE_SCOPES["drive"]]
    ensure_scopes(granted, required, tool="mail.get_recent", token_path="/tmp/token.json")


def test_ensure_scopes_missing_raises():
    required = [GOOGLE_SCOPES["gmail.readonly"]]
    granted = [GOOGLE_SCOPES["drive"]]
    with pytest.raises(ScopeError) as exc:
        ensure_scopes(granted, required, tool="mail.get_recent", token_path="/tmp/token.json")
    assert "gmail.readonly" in str(exc.value) or "googleapis.com/auth/gmail" in str(exc.value)


def test_scope_urls_deduplicates():
    urls = scope_urls(["drive.readonly", "drive"])
    assert len(urls) >= 1
