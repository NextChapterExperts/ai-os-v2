"""Tests for Intent Router catalog, search priority, and meeting open loop integration."""

from __future__ import annotations

import os
import sys
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.intent_router import route_intent
from core.orchestrator.handlers import daily_open_loops
from core.orchestrator.meetings_store import create_meeting, delete_meeting


def test_explicit_search_overrides_open_loops_keywords():
    # User query from bug report
    intent1 = route_intent("ich suche nach : Gibt es offene Punkte aus Meetings")
    assert intent1 == "unified_search"

    intent2 = route_intent("suche nach offenen To-Dos im Projekt")
    assert intent2 == "unified_search"

    intent3 = route_intent("durchsuche dateien nach agenda")
    assert intent3 == "unified_search"


def test_meeting_specific_queries_route_to_daily_open_loops():
    intent1 = route_intent("Gibt es offene Punkte aus Meetings?")
    assert intent1 == "daily_open_loops"

    intent2 = route_intent("Meeting To-Dos für diese Woche")
    assert intent2 == "daily_open_loops"

    intent3 = route_intent("Welche Beschlüsse gab es im Meeting?")
    assert intent3 in {"memory_ask", "daily_open_loops"}


def test_standard_prompt_catalog_daily_open_loops():
    prompts = [
        "Was ist noch offen?",
        "Was steht noch aus?",
        "Was liegt an?",
        "Was müsste gemacht werden?",
        "Was sind wichtige Punkte für heute?",
        "Was steht heute an?",
        "Meine Open Loops",
        "Was muss ich heute noch machen?",
    ]
    for prompt in prompts:
        intent = route_intent(prompt)
        assert intent == "daily_open_loops", f"Failed for prompt: '{prompt}' (got {intent})"


def test_standard_prompt_catalog_project_status():
    prompts = [
        "Wie ist der Stand zum Projekt AI-OS?",
        "Status von SAP APIM Training",
        "Projektstand 1100-AI-OS",
        "Was haben wir bisher gemacht?",
    ]
    for prompt in prompts:
        intent = route_intent(prompt)
        assert intent == "memory_ask", f"Failed for prompt: '{prompt}' (got {intent})"


@pytest.mark.asyncio
async def test_daily_open_loops_includes_meeting_todos(tmp_path, monkeypatch):
    tenant_id = "test-catalog-tenant"
    
    # Create test meeting with open To-Do
    meeting_data = {
        "title": "Abschluss-Meeting Ende August",
        "held_at": "2026-08-25T10:00:00Z",
        "participants": "Peter, Alex",
        "summary": "Terminvereinbarung für Ende August vorbereiten.",
        "todos": [
            {"task": "Terminvereinbarung für Ende August bestätigen", "done": False}
        ],
    }
    m = create_meeting(tenant_id, meeting_data)
    
    try:
        context_bundle = {"system": {"tenant": {"id": tenant_id}}}
        res = await daily_open_loops.run(context_bundle, tenant_id, {})
        assert "Tagesübersicht" in res["answer"]
        assert "Offene Aufgaben aus Meetings" in res["answer"]
        assert "Terminvereinbarung für Ende August bestätigen" in res["answer"]
        assert "[Meetings öffnen](/meetings)" in res["answer"]
        assert "[Projekt-Portfolio öffnen](/portfolio)" in res["answer"]
    finally:
        delete_meeting(m["id"], tenant_id)


@pytest.mark.asyncio
async def test_unified_search_finds_meeting_todos():
    tenant_id = "test-search-todo-tenant"
    meeting_data = {
        "title": "Austausch mit SAP BAIP Abteilung",
        "held_at": "2026-08-25T10:00:00Z",
        "participants": "Peter",
        "summary": "Diskussion zu Simulatoren",
        "todos": [
            {
                "text": "Termin erstellen für Ende August um das gesamte Projekt vorzustellen - Blog Simulator , Workflowsimulator  etc.",
                "done": False,
            }
        ],
    }
    m = create_meeting(tenant_id, meeting_data)
    try:
        from core.orchestrator.handlers import unified_search

        # Search by keyword in To-Do text
        res = await unified_search.run({}, tenant_id, {"query": "Blog Simulator"})
        assert res["sourceCount"] > 0
        hits = [s for s in res["sources"] if s.get("source_type") == "meeting"]
        assert len(hits) > 0
        assert "Austausch mit SAP BAIP Abteilung" in hits[0]["title"]
        assert "Blog Simulator" in hits[0]["snippet"]
    finally:
        delete_meeting(m["id"], tenant_id)


@pytest.mark.asyncio
async def test_daily_open_loops_formatting_and_navigation_links():
    tenant_id = "test-formatting-tenant"
    context_bundle = {"system": {"tenant": {"id": tenant_id}}}
    res = await daily_open_loops.run(context_bundle, tenant_id, {})
    assert "Tagesübersicht — Offene Punkte, Termine & Projekte:" in res["answer"]
    assert "📌 **Direkt-Absprung:**" in res["answer"]
    assert "[Meetings-Übersicht öffnen](/meetings)" in res["answer"]
    assert "[Projekt-Portfolio öffnen](/portfolio)" in res["answer"]


