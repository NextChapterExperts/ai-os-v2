"""OAuth-Scope-Registry — v2-Fix für v1-Bug ce07801 (Scopes vor MCP-Call prüfen)."""

from __future__ import annotations

from typing import Iterable

# Kanonische Scope-URLs (Google API)
GOOGLE_SCOPES = {
    "calendar.readonly": "https://www.googleapis.com/auth/calendar.readonly",
    "calendar": "https://www.googleapis.com/auth/calendar",
    "gmail.readonly": "https://www.googleapis.com/auth/gmail.readonly",
    "gmail.modify": "https://www.googleapis.com/auth/gmail.modify",
    "drive": "https://www.googleapis.com/auth/drive",
    "drive.readonly": "https://www.googleapis.com/auth/drive.readonly",
    "spreadsheets": "https://www.googleapis.com/auth/spreadsheets",
    "tasks": "https://www.googleapis.com/auth/tasks",
}

# MCP-Tool → benötigte Scope-Schlüssel
TOOL_SCOPE_KEYS: dict[str, list[str]] = {
    "mail.get_recent": ["gmail.readonly"],
    "mail.get_by_id": ["gmail.readonly"],
    "mail.preview_invoices": ["gmail.readonly"],
    "mail.run_invoices": ["gmail.readonly", "spreadsheets", "drive"],
    "mail.export_steuer": ["gmail.readonly", "drive"],
    "mail.send": ["gmail.modify"],
    "mail.status": ["gmail.readonly"],
    "calendar.get_today": ["calendar.readonly"],
    "calendar.get_week": ["calendar.readonly"],
    "calendar.list_attendees": ["calendar.readonly"],
    "calendar.get_event": ["calendar.readonly"],
    "calendar.create_event": ["calendar"],
    "calendar.list_today": ["calendar.readonly"],
    "drive.list_folder": ["drive.readonly", "drive"],
    "drive.export_document": ["drive.readonly", "drive"],
    "drive.list_sources": ["drive.readonly", "drive"],
    "drive.poll_chats": ["drive.readonly", "drive"],
    "sheets.read": ["spreadsheets"],
    "sheets.write": ["spreadsheets"],
}


class ScopeError(RuntimeError):
    """Token fehlt erforderliche OAuth-Scopes für ein MCP-Tool."""

    def __init__(self, tool: str, missing: list[str], token_path: str) -> None:
        self.tool = tool
        self.missing = missing
        self.token_path = token_path
        super().__init__(
            f"MCP-Tool '{tool}' benötigt Scopes {missing}, "
            f"Token {token_path} deckt sie nicht ab. "
            "Erneuern: python scripts/test_google_connection.py"
        )


def scope_urls(keys: Iterable[str]) -> list[str]:
    out: list[str] = []
    for key in keys:
        url = GOOGLE_SCOPES.get(key)
        if url and url not in out:
            out.append(url)
    return out


def tool_required_scopes(server: str, tool: str) -> list[str]:
    """Liefert die OAuth-Scope-URLs für ein MCP-Tool."""
    key = f"{server}.{tool}"
    keys = TOOL_SCOPE_KEYS.get(key, [])
    return scope_urls(keys)


def ensure_scopes(
    granted: Iterable[str] | None,
    required: Iterable[str],
    *,
    tool: str,
    token_path: str,
) -> None:
    """Wirft ScopeError wenn granted die required URLs nicht enthält."""
    granted_set = set(granted or [])
    missing = [s for s in required if s not in granted_set]
    if missing:
        raise ScopeError(tool, missing, token_path)
