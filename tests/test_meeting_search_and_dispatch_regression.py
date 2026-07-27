"""Regression test suite for Meeting To-Do search, Intent Router priority, and Daily Open Loops compute mode."""

from __future__ import annotations

import os
import sys
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.orchestrator.intent_router import route_intent
from core.orchestrator.meetings_store import create_meeting, update_meeting, delete_meeting, list_meetings
from core.orchestrator.handlers import unified_search, daily_open_loops


def test_meetings_store_sql_search_by_todo_text():
    tenant_id = "test-sql-todo-tenant"
    meeting_data = {
        "title": "Architektur-Sprint SAP BAIP",
        "held_at": "2026-08-30T14:00:00Z",
        "participants": "Peter, Alex",
        "summary": "Vorstellung der Simulatoren",
        "todos": [
            {
                "text": "Termin erstellen für Ende August um das gesamte Projekt vorzustellen - Blog Simulator , Workflowsimulator etc.",
                "done": False,
            }
        ],
    }
    m = create_meeting(tenant_id, meeting_data)
    try:
        # Search by 'Blog Simulator'
        hits1 = list_meetings(tenant_id, q="Blog Simulator")
        assert len(hits1) == 1
        assert hits1[0]["id"] == m["id"]

        # Search by 'Workflowsimulator'
        hits2 = list_meetings(tenant_id, q="Workflowsimulator")
        assert len(hits2) == 1
        assert hits2[0]["id"] == m["id"]

        # Search by 'Ende August'
        hits3 = list_meetings(tenant_id, q="Ende August")
        assert len(hits3) == 1
        assert hits3[0]["id"] == m["id"]
    finally:
        delete_meeting(m["id"], tenant_id)


def test_meetings_store_update_indexes_memory():
    tenant_id = "test-update-index-tenant"
    meeting_data = {
        "title": "Vorab-Besprechung",
        "held_at": "2026-08-15T09:00:00Z",
        "participants": "Peter",
        "summary": "Initiales Briefing",
        "todos": [],
    }
    m = create_meeting(tenant_id, meeting_data)
    try:
        updated = update_meeting(m["id"], tenant_id, {
            "summary": "Aktualisiertes Briefing",
            "todos": [{"text": "Projekt-Präsentation im Team reviewen", "done": False}]
        })
        assert updated is not None
        hits = list_meetings(tenant_id, q="Projekt-Präsentation")
        assert len(hits) == 1
        assert hits[0]["id"] == m["id"]
    finally:
        delete_meeting(m["id"], tenant_id)


@pytest.mark.asyncio
async def test_unified_search_includes_meeting_store_source():
    tenant_id = "test-unified-meeting-tenant"
    meeting_data = {
        "title": "Roadmap Alignment Q3",
        "held_at": "2026-08-28T11:00:00Z",
        "participants": "Peter",
        "summary": "Diskussion über Release-Planung",
        "todos": [
            {"text": "Refactoring des Search Providers durchführen", "done": False}
        ],
    }
    m = create_meeting(tenant_id, meeting_data)
    try:
        res = await unified_search.run({}, tenant_id, {"query": "Refactoring des Search Providers"})
        assert res["kind"] == "search"
        meeting_hits = [s for s in res["sources"] if s.get("source_type") == "meeting"]
        assert len(meeting_hits) > 0
        assert "Roadmap Alignment Q3" in meeting_hits[0]["title"]
    finally:
        delete_meeting(m["id"], tenant_id)


def test_intent_router_meeting_todo_queries():
    test_queries = [
        ("Gibt es offene Punkte aus Meetings?", "daily_open_loops"),
        ("Gibt es offene Punkte aus den Meetings?", "daily_open_loops"),
        ("Meeting To-Dos für diese Woche", "daily_open_loops"),
        ("ich suche nach : Gibt es offene Punkte aus Meetings", "unified_search"),
    ]
    for query, expected_intent in test_queries:
        actual = route_intent(query)
        assert actual == expected_intent, f"Query '{query}' expected '{expected_intent}' but got '{actual}'"


@pytest.mark.asyncio
async def test_daily_open_loops_respects_custom_compute_mode(monkeypatch):
    tenant_id = "test-compute-mode-tenant"
    captured_params = {}

    async def mock_memory_ask_run(context_bundle, t_id, params):
        captured_params.update(params)
        return {"answer": "Mocked memory response"}

    monkeypatch.setattr("core.orchestrator.handlers.memory_ask.run", mock_memory_ask_run)

    context_bundle = {"system": {"tenant": {"id": tenant_id}}}
    await daily_open_loops.run(context_bundle, tenant_id, {"compute_mode": "balanced"})

    assert captured_params.get("compute_mode") == "balanced"
