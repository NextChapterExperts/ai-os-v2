"""Mail MCP stub — placeholder until real MCP mail adapter (Phase 2)."""

from __future__ import annotations

from typing import Any


async def list_open_actions(tenant_id: str) -> dict[str, Any]:
    # Deterministic stub actions so daily_open_loops / mail_triage are testable
    return {
        "status": "stub",
        "status_note": (
            "Mail-Agent: MCP-Adapter noch Stub "
            "(kein IMAP). Nächster Schritt: core/mcp-gateway + mail adapter."
        ),
        "actions": [
            {
                "id": "mail-stub-1",
                "subject": "Hochschule — Kickoff Unterlagen",
                "action": "Antwort entwerfen / Termin bestätigen",
                "related_engagement": "eng-studenten-ss26",
            },
            {
                "id": "mail-stub-2",
                "subject": "SAP API Mgmt — Teilnehmerliste",
                "action": "Liste prüfen und Agenda anhängen",
                "related_engagement": "eng-sap-apim-kw-next",
            },
        ],
        "tenant_id": tenant_id,
    }
