"""Meetings-Fachagent — Contract-, Registry- und API-Regressionstests.

Abdeckt grundlegende Fehlerklassen:
- Workflow nicht registriert
- UI-Schema ohne Meeting-Picker (nur technische ID)
- MCP-Tools fehlen in Allowlist
- Meeting-Liste ohne Titel/Teilnehmer
- Zusammenfassung-Commit nicht über MCP
"""

from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

import core.mcp_gateway.adapters  # noqa: F401 — Handler registrieren
from agents.meetings.agent import MeetingsAgent
from agents.meetings.dataproducts import MeetingsAgentRequest, MeetingsAgentUserInput
from core.mcp_gateway.adapters.registry import allowlist, dispatch
from core.orchestrator.server import app

client = TestClient(app)


@pytest.fixture()
def meetings_db(tmp_path, monkeypatch):
    db = tmp_path / "meetings.db"
    att = tmp_path / "attachments"
    monkeypatch.setenv("AIOS_MEETINGS_DB", str(db))
    monkeypatch.setenv("AIOS_MEETINGS_ATTACHMENTS_DIR", str(att))
    yield db


def test_meetings_workflow_registry_contract():
    """Meetings-Agent muss in der Workflow-Registry mit UI-Schema registriert sein."""
    import core.workflow_engine.meetings_workflows  # noqa: F401
    from core.workflow_engine.generic_runner import get_workflow_registry

    registry = get_workflow_registry()
    assert "meetings-agent" in registry
    wf = registry["meetings-agent"]
    assert wf.input_schema.__name__ == "MeetingsAgentUserInput"
    assert wf.output_schema.__name__ == "MeetingsAgentReport"
    assert wf.workflow_id == "meetings-agent"


def test_meetings_ui_schema_meeting_picker_not_raw_id():
    """Zusammenfassung: meeting_id muss Meeting-Picker sein — nicht nur technische ID."""
    schema = MeetingsAgentUserInput.get_ui_schema()
    props = schema.get("properties", {})
    assert "meeting_id" in props
    meeting_field = props["meeting_id"]
    assert meeting_field.get("title") == "Meeting auswählen"
    assert meeting_field.get("x-widget") == "meeting-picker"
    assert meeting_field.get("x-visible-when") == {"aufgabe": "zusammenfassung_speichern"}
    assert "workflow_run_id" not in props
    assert "dp_id" not in props
    assert "tenant_id" not in props


def test_meetings_user_input_maps_operations():
    """UserInput → AgentRequest: Aufgabe und Live/Dry-Run korrekt mappen."""
    ui = MeetingsAgentUserInput(
        aufgabe="zusammenfassung_speichern",
        run_mode="live",
        meeting_id=" meet-abc ",
        summary="  Wichtige Entscheidung. ",
    )
    req = ui.to_agent_request()
    assert req.operation == "zusammenfassung_speichern"
    assert req.dry_run is False
    assert req.meeting_id == "meet-abc"
    assert req.summary == "Wichtige Entscheidung."


def test_mcp_meetings_tools_in_allowlist():
    """MCP-Allowlist muss alle Meetings-Tools für den Fachagenten enthalten."""
    tools = allowlist().get("meetings") or []
    for tool in ("sync_from_calendar", "commit_to_company_brain", "person_stats", "status"):
        assert tool in tools, f"meetings.{tool} fehlt in MCP-Allowlist"


def test_workflows_registry_api_includes_meetings_agent():
    """GET /v1/workflows/registry liefert meetings-agent inkl. Meeting-Picker-Schema."""
    res = client.get("/v1/workflows/registry")
    assert res.status_code == 200
    body = res.json()
    assert body.get("count", 0) >= 3
    workflows = body.get("workflows") or {}
    assert "meetings-agent" in workflows
    props = workflows["meetings-agent"]["input_schema"].get("properties", {})
    assert props["meeting_id"].get("x-widget") == "meeting-picker"


@pytest.mark.asyncio
async def test_meetings_agent_sync_mcp_only(meetings_db):
    """termine_abrufen: Agent ruft ausschließlich meetings.sync_from_calendar auf."""
    calls: list[tuple[str, str, dict]] = []

    class FakeMCP:
        async def call(self, server, tool, args, timeout=60.0):
            calls.append((server, tool, args))
            return {
                "ok": True,
                "since_date": "2026-07-01",
                "until_date": "2026-08-03",
                "imported": 1,
                "updated": 0,
                "skipped": 0,
                "dry_run": True,
                "meetings": [
                    {
                        "meeting_id": "meet-1",
                        "title": "Launch Review",
                        "held_at": "2026-07-15T10:00:00+02:00",
                        "participants_label": "Alice, Bob",
                        "has_summary": False,
                        "attendees": [
                            {"email": "alice@example.com", "name": "Alice"},
                            {"email": "bob@corp.de", "name": "Bob"},
                        ],
                    }
                ],
                "person_stats": [],
                "forecast_next_month": [],
                "summary": "OK",
            }

    agent = MeetingsAgent(ctx=None, mcp=FakeMCP())
    req = MeetingsAgentRequest(
        tenant_id="nextchapter",
        produced_by="meetings-agent",
        operation="termine_abrufen",
        dry_run=True,
    )
    report = await agent.run(req)
    assert len(calls) == 1
    assert calls[0][0] == "meetings"
    assert calls[0][1] == "sync_from_calendar"
    assert len(report.meetings) == 1
    assert report.meetings[0].title == "Launch Review"
    assert report.meetings[0].participants_label == "Alice, Bob"
    assert report.meetings[0].meeting_id == "meet-1"


@pytest.mark.asyncio
async def test_meetings_agent_commit_mcp_only(meetings_db):
    """zusammenfassung_speichern: Agent ruft meetings.commit_to_company_brain auf."""
    calls: list[tuple[str, str, dict]] = []

    class FakeMCP:
        async def call(self, server, tool, args, timeout=60.0):
            calls.append((server, tool, args))
            return {
                "ok": True,
                "dry_run": True,
                "meeting_id": args["meeting_id"],
                "kg_node_type": "org:Meeting",
                "kg_external_id": "meet:launch",
                "summary": args["summary"],
            }

    agent = MeetingsAgent(ctx=None, mcp=FakeMCP())
    req = MeetingsAgentRequest(
        tenant_id="nextchapter",
        produced_by="meetings-agent",
        operation="zusammenfassung_speichern",
        meeting_id="meet-1",
        summary="Entscheidung: Go-Live im August.",
        dry_run=True,
    )
    report = await agent.run(req)
    assert len(calls) == 1
    assert calls[0] == (
        "meetings",
        "commit_to_company_brain",
        {
            "tenant_id": "nextchapter",
            "meeting_id": "meet-1",
            "summary": "Entscheidung: Go-Live im August.",
            "dry_run": True,
        },
    )
    assert report.operation == "zusammenfassung_speichern"
    assert report.kg_node_type == "org:Meeting"
    assert report.committed_meeting_id == "meet-1"


def test_meetings_list_api_human_readable_fields(meetings_db):
    """GET /v1/meetings liefert Titel, Datum, Teilnehmer — nicht nur ID."""
    from core.orchestrator import meetings_store as ms

    ms.upsert_calendar_meeting(
        "nextchapter",
        calendar_event_id="gcal-api-1",
        title="SAP BAIP Austausch",
        held_at="2026-07-27T13:00:00+02:00",
        attendees=[
            {"email": "juergen@example.com", "name": "Juergen Bauer"},
            {"email": "tob@example.com", "name": "Tob Mueller"},
        ],
        dry_run=False,
    )

    res = client.get("/v1/meetings?tenant_id=nextchapter&limit=10")
    assert res.status_code == 200
    meetings = res.json().get("meetings") or []
    assert len(meetings) >= 1
    row = next(m for m in meetings if m.get("title") == "SAP BAIP Austausch")
    assert row.get("held_at")
    assert "Juergen" in (row.get("participants") or "")
    assert row.get("id")


def test_workflow_execute_meetings_agent_not_unregistered(meetings_db, monkeypatch):
    """POST /v1/workflow/execute darf meetings-agent nicht mit 'nicht registriert' ablehnen."""
    monkeypatch.setattr(
        "core.google.meetings.sync.google_auth.secrets_configured",
        lambda: False,
    )
    res = client.post(
        "/v1/workflow/execute",
        json={
            "workflow_id": "meetings-agent",
            "tenant_id": "nextchapter",
            "payload": {
                "aufgabe": "termine_abrufen",
                "run_mode": "dry_run",
                "since_date": "2026-07-01",
                "include_forecast": "yes",
            },
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("workflow_id") == "meetings-agent"
    assert body.get("status") == "completed"
    assert "output_dp" in body


def test_mcp_commit_requires_meeting_id_and_summary(meetings_db):
    """commit_to_company_brain: Pflichtfelder meeting_id und summary."""
    missing_id = dispatch(
        "meetings",
        "commit_to_company_brain",
        {"tenant_id": "nextchapter", "summary": "Text", "dry_run": True},
    )
    assert missing_id["ok"] is False
    assert missing_id["error"] == "missing_meeting_id"

    missing_summary = dispatch(
        "meetings",
        "commit_to_company_brain",
        {"tenant_id": "nextchapter", "meeting_id": "x", "dry_run": True},
    )
    assert missing_summary["ok"] is False
    assert missing_summary["error"] == "missing_summary"


def test_console_fallback_schema_has_meeting_picker():
    """Console-Fallback (agents/page.tsx) muss meeting-picker für meeting_id definieren."""
    page_path = os.path.join(REPO, "core/console-web/src/app/agents/page.tsx")
    page = open(page_path, encoding="utf-8").read()
    assert '"x-widget": "meeting-picker"' in page
    assert "Meeting auswählen" in page
    assert "meetings-agent" in page
