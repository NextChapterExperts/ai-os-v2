"""Tests: Meetings-Kalender-Sync, Person-Stats, MCP-Adapter."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def meetings_db(tmp_path, monkeypatch):
    db = tmp_path / "meetings.db"
    att = tmp_path / "attachments"
    monkeypatch.setenv("AIOS_MEETINGS_DB", str(db))
    monkeypatch.setenv("AIOS_MEETINGS_ATTACHMENTS_DIR", str(att))
    yield db


def test_upsert_calendar_meeting_creates_and_updates(meetings_db):
    from core.orchestrator import meetings_store as ms

    attendees = [{"email": "alice@example.com", "name": "Alice"}, {"email": "bob@corp.de", "name": "Bob"}]
    action, row = ms.upsert_calendar_meeting(
        "nextchapter",
        calendar_event_id="gcal-abc123",
        title="Launch Review",
        held_at="2026-07-15T10:00:00+02:00",
        end_at="2026-07-15T11:00:00+02:00",
        location="Zoom",
        attendees=attendees,
        dry_run=False,
    )
    assert action == "created"
    assert row is not None
    assert row["title"] == "Launch Review"
    assert row["calendar_event_id"] == "gcal-abc123"
    assert row["source"] == "calendar"

    action2, row2 = ms.upsert_calendar_meeting(
        "nextchapter",
        calendar_event_id="gcal-abc123",
        title="Launch Review (updated)",
        held_at="2026-07-15T10:00:00+02:00",
        attendees=attendees,
        dry_run=False,
    )
    assert action2 == "updated"
    assert row2["title"] == "Launch Review (updated)"

    found = ms.find_meeting_by_calendar_event_id("gcal-abc123", "nextchapter")
    assert found is not None
    assert found["id"] == row["id"]


def test_upsert_preserves_summary_when_present(meetings_db):
    from core.orchestrator import meetings_store as ms

    ms.upsert_calendar_meeting(
        "nextchapter",
        calendar_event_id="gcal-xyz",
        title="Standup",
        held_at="2026-07-02T09:00:00+02:00",
        attendees=[{"email": "a@x.de", "name": "A"}],
        dry_run=False,
    )
    m = ms.find_meeting_by_calendar_event_id("gcal-xyz", "nextchapter")
    assert m
    ms.update_meeting(m["id"], "nextchapter", {"summary": "Wichtige Entscheidung getroffen."})

    _, row = ms.upsert_calendar_meeting(
        "nextchapter",
        calendar_event_id="gcal-xyz",
        title="Standup Neu",
        held_at="2026-07-02T09:30:00+02:00",
        attendees=[{"email": "a@x.de", "name": "A"}],
        dry_run=False,
    )
    assert row["summary"] == "Wichtige Entscheidung getroffen."
    assert row["title"] == "Standup Neu"


def test_person_meeting_stats(meetings_db):
    from core.orchestrator import meetings_store as ms

    for i, day in enumerate(["2026-07-01", "2026-07-10", "2026-08-01"], start=1):
        ms.upsert_calendar_meeting(
            "nextchapter",
            calendar_event_id=f"gcal-stat-{i}",
            title=f"Sync {i}",
            held_at=f"{day}T14:00:00+02:00",
            attendees=[{"email": "partner@firma.de", "name": "Partner"}], 
            dry_run=False,
        )

    stats = ms.compute_person_meeting_stats("nextchapter", since_date="2026-07-01")
    partner = next(s for s in stats if s["email"] == "partner@firma.de")
    assert partner["meeting_count"] == 3
    assert partner["last_meeting_at"].startswith("2026-08-01")

    lookup = ms.lookup_person_meeting_stats("nextchapter", "partner@firma.de")
    assert lookup is not None
    assert lookup["meeting_count"] == 3

    none = ms.lookup_person_meeting_stats("nextchapter", "unbekannt@x.de")
    assert none is None


def test_sync_stub_without_oauth(monkeypatch):
    from core.google.meetings.sync import sync_calendar_to_inbox

    monkeypatch.setattr(
        "core.google.meetings.sync.google_auth.secrets_configured",
        lambda: False,
    )
    result = sync_calendar_to_inbox(since_date="2026-07-01", dry_run=True)
    assert result["ok"] is True
    assert result["status"] == "stub"
    assert result["since_date"] == "2026-07-01"


def test_mcp_meetings_sync_dry_run(monkeypatch, meetings_db):
    from core.mcp_gateway.adapters.registry import dispatch

    monkeypatch.setattr(
        "core.google.meetings.sync.google_auth.secrets_configured",
        lambda: False,
    )
    result = dispatch(
        "meetings",
        "sync_from_calendar",
        {"tenant_id": "nextchapter", "since_date": "2026-07-01", "dry_run": True},
    )
    assert result["ok"] is True
    assert result["since_date"] == "2026-07-01"


def test_meetings_agent_mcp_only(monkeypatch, meetings_db):
    import asyncio
    from agents.meetings.agent import MeetingsAgent
    from agents.meetings.dataproducts import MeetingsAgentRequest

    calls = []

    class FakeMCP:
        async def call(self, server, tool, args, timeout=60.0):
            calls.append((server, tool, args))
            return {
                "ok": True,
                "since_date": "2026-07-01",
                "until_date": "2026-08-03",
                "imported": 2,
                "updated": 1,
                "skipped": 0,
                "dry_run": True,
                "meetings": [],
                "person_stats": [{"email": "a@b.de", "name": "A", "meeting_count": 2,
                                  "first_meeting_at": "2026-07-01", "last_meeting_at": "2026-07-15",
                                  "meeting_ids": [], "meeting_titles": []}],
                "forecast_next_month": [{"held_at": "2026-08-10", "title": "Next", "location": "",
                                         "attendee_emails": ["a@b.de"], "calendar_event_id": "x"}],
                "summary": "OK",
            }

    agent = MeetingsAgent(ctx=None, mcp=FakeMCP())
    req = MeetingsAgentRequest(tenant_id="nextchapter", produced_by="meetings-agent", dry_run=True)
    report = asyncio.run(agent.run(req))
    assert calls[0][0] == "meetings"
    assert calls[0][1] == "sync_from_calendar"
    assert report.imported == 2
    assert len(report.person_stats) == 1
    assert report.person_stats[0].meeting_count == 2
    assert len(report.forecast_next_month) == 1


def test_mcp_commit_dry_run(meetings_db):
    from core.mcp_gateway.adapters.registry import dispatch
    from core.orchestrator import meetings_store as ms
    from core.orchestrator.dataproducts import OrgMeeting
    from core.orchestrator.dp_service import _ingest_recommended

    ms.upsert_calendar_meeting(
        "nextchapter",
        calendar_event_id="gcal-commit-1",
        title="Brain Test",
        held_at="2026-07-20T10:00:00+02:00",
        attendees=[{"email": "a@test.de", "name": "A"}],
        dry_run=False,
    )
    m = ms.find_meeting_by_calendar_event_id("gcal-commit-1", "nextchapter")
    assert m
    result = dispatch(
        "meetings",
        "commit_to_company_brain",
        {
            "tenant_id": "nextchapter",
            "meeting_id": m["id"],
            "summary": "Wichtige Punkte.",
            "dry_run": True,
        },
    )
    assert result["ok"] is True
    assert result.get("dry_run") is True
    assert "Wichtige Punkte" in result.get("summary", "") or "Zusammenfassung" in result.get("summary", "")

    org = OrgMeeting(
        tenant_id="nextchapter",
        produced_by="meetings-agent",
        meeting_id=m["id"],
        title="Brain Test",
        held_at="2026-07-20T10:00:00+02:00",
        summary="Wichtige Punkte.",
    )
    assert _ingest_recommended(org) is True


def test_meetings_user_input_requires_meeting_and_summary():
    from agents.meetings.dataproducts import MeetingsAgentUserInput
    import pytest

    with pytest.raises(ValueError, match="Meeting"):
        MeetingsAgentUserInput(aufgabe="zusammenfassung_speichern", meeting_id="", summary="Text")

    with pytest.raises(ValueError, match="Zusammenfassung"):
        MeetingsAgentUserInput(aufgabe="zusammenfassung_speichern", meeting_id="meet-1", summary="")
