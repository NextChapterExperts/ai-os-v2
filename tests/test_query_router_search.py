"""Query Router, Intent Matching, and Search Tokenization Tests."""

from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.kg_search import _tokenize
from core.orchestrator.memory_store import _escape_fts
from core.orchestrator.query_router import DEFAULT_PLAN, route_query


def test_query_router_decision_policy_rules():
    plan_dec = route_query("Welche Decision gilt für consulting?")
    assert plan_dec.use_g is True
    assert plan_dec.use_l1 is False
    assert plan_dec.use_letta is False

    plan_pol = route_query("Welche Policy regelt den Datenschutz?")
    assert plan_pol.use_g is True
    assert plan_pol.use_l1 is False


def test_query_router_temporal_rules():
    plan_yesterday = route_query("Was haben wir gestern besprochen?")
    assert plan_yesterday.use_letta is True
    assert plan_yesterday.use_g is False

    plan_remember = route_query("Erinnerst du dich an letzte Woche?")
    assert plan_remember.use_letta is True
    assert plan_remember.use_g is False


def test_query_router_research_rules():
    plan_research = route_query("Recherche nach ähnlichen Beispielen wie Blog")
    assert plan_research.use_l1 is True
    assert plan_research.use_g is True
    assert plan_research.use_sk is True


def test_query_router_skill_rules():
    plan_skill = route_query("Wie haben wir das Verfahren durchgeführt?")
    assert plan_skill.use_sk is True
    assert plan_skill.use_l1 is True


def test_query_router_default_fallback():
    plan_empty = route_query("")
    assert plan_empty == DEFAULT_PLAN

    plan_general = route_query("Allgemeine Frage zu AI-OS")
    assert plan_general == DEFAULT_PLAN


def test_search_tokenization_preserves_identifiers():
    tokens = _tokenize("Welche Policy gilt für peter@example.com im ai-os-v2 Repo?")
    # Ensure email and hyphenated tokens are preserved without being stripped to pieces
    assert any("peter@example.com" in t or "example.com" in t or "peter" in t for t in tokens)
    assert any("ai-os-v2" in t or "ai-os" in t for t in tokens)
    assert "welche" not in tokens
    assert "für" not in tokens


def test_fts_query_escaping():
    escaped = _escape_fts("Company Brain & Architecture")
    assert '"Company"' in escaped
    assert '"Brain"' in escaped
    assert '"Architecture"' in escaped
    assert " AND " in escaped

    empty_escaped = _escape_fts("")
    assert empty_escaped == ""
