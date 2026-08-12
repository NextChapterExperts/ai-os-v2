"""AI-OS v2 — Automated Test Suite for Recherche-Agent Prototype (20 Boundary Tests).

Covers lower & upper boundary conditions, model overrides, prompt inspection capture,
anonymity metadata, SDK DataProducts, and Orchestrator integration.
"""

from __future__ import annotations

import pytest
import asyncio
from typing import Any

from agents.research.agent import ResearchAgent, ResearchInput, ResearchResult
from core.orchestrator.handlers import research_handler
from core.orchestrator.intent_router import route_intent
from core.orchestrator.dispatch import dispatch


# Dummy context for Agent testing
class MockAgentContext:
    tenant_id = "nextchapter"


class MockMCPAdapter:
    async def call(self, server: str, tool: str, args: dict[str, Any]) -> Any:
        if server == "qdrant_search":
            return [
                {"id": "doc1", "title": "Lokales Brain Doc", "text": "SAP Migration Leitfaden NCE"}
            ]
        if server == "web_search":
            return [
                {
                    "title": "SearXNG Web Result",
                    "url": "https://searxng.local/test",
                    "snippet": "Anonymes Testergebnis",
                }
            ]
        return []


# --- 20 Boundary Test Cases ---

# 1. Lower boundary: Empty query
@pytest.mark.asyncio
async def test_01_empty_query_boundary():
    agent = ResearchAgent(MockAgentContext(), MockMCPAdapter())
    inp = ResearchInput(tenant_id="nextchapter", produced_by="test", query="")
    res = await agent.run(inp)
    assert isinstance(res, ResearchResult)
    assert res.confidence == 0.0
    assert res.summary == "Keine Suchanfrage angegeben."


# 2. Lower boundary: Pure gibberish query
@pytest.mark.asyncio
async def test_02_gibberish_query_boundary():
    res = await research_handler.run({}, "nextchapter", {"query": "asdfjkl; 12345 !@#$%^&*()"})
    assert res["query"] == "asdfjkl; 12345 !@#$%^&*()"
    assert "llmContext" in res
    assert res["anonymity_active"] is True


# 3. Lower boundary: Single character query
@pytest.mark.asyncio
async def test_03_single_char_query():
    agent = ResearchAgent(MockAgentContext(), MockMCPAdapter())
    inp = ResearchInput(tenant_id="nextchapter", produced_by="test", query="a")
    res = await agent.run(inp)
    assert isinstance(res, ResearchResult)
    assert res.query == "a"


# 4. Lower boundary: SQL Injection attempt
@pytest.mark.asyncio
async def test_04_sql_injection_attempt():
    payload = "DROP TABLE users; SELECT * FROM credentials;"
    res = await research_handler.run({}, "nextchapter", {"query": payload})
    assert res["query"] == payload
    # Must handle safely without breaking
    assert "summary" in res


# 5. Lower boundary: Script XSS Tag Injection attempt
@pytest.mark.asyncio
async def test_05_script_injection_attempt():
    payload = "<script>alert('xss')</script>"
    res = await research_handler.run({}, "nextchapter", {"query": payload})
    assert res["query"] == payload
    assert "llmContext" in res


# 6. Lower boundary: Extremely long text query (>5,000 chars)
@pytest.mark.asyncio
async def test_06_extreme_long_query():
    long_query = "Recherche " * 600
    res = await research_handler.run({}, "nextchapter", {"query": long_query})
    assert len(res["query"]) > 5000
    assert res["llmContext"]["prompt"]["contextCharCount"] > 5000


# 7. Upper boundary: Complex multi-part technical query
@pytest.mark.asyncio
async def test_07_complex_technical_query():
    complex_q = "Comparison of SAP S/4HANA Cloud vs Oracle Cloud ERP migration performance, database latency, and licensing bottlenecks in 2026"
    res = await research_handler.run({}, "nextchapter", {"query": complex_q, "depth": "deep"})
    assert res["query"] == complex_q
    assert len(res["sub_questions"]) >= 3


# 8. Upper boundary: Multilingual mixed query
@pytest.mark.asyncio
async def test_08_multilingual_mixed_query():
    mixed_q = "Enterprise KI-OS Architecture & DSGVO Compliance in Deutschland"
    res = await research_handler.run({}, "nextchapter", {"query": mixed_q})
    assert res["confidence"] > 0.0


# 9. Upper boundary: Entity extraction targeted query
@pytest.mark.asyncio
async def test_09_entity_extraction_query():
    res = await research_handler.run({}, "nextchapter", {"query": "Welche Decisions gibt es zum Offering AI-OS?"})
    assert "sources" in res


# 10. Model override: Qwen 2.5 Coder 14B
@pytest.mark.asyncio
async def test_10_model_override_qwen():
    res = await research_handler.run({}, "nextchapter", {"query": "Test", "model": "qwen2.5-coder:14b"})
    assert res["model_used"] == "qwen2.5-coder:14b"
    assert res["llmContext"]["routing"]["model"] == "qwen2.5-coder:14b"


# 11. Model override: Mistral Nemo 12B
@pytest.mark.asyncio
async def test_11_model_override_mistral():
    res = await research_handler.run({}, "nextchapter", {"query": "Test", "model": "mistral-nemo:12b"})
    assert res["model_used"] == "mistral-nemo:12b"


# 12. Compute mode: sovereign
@pytest.mark.asyncio
async def test_12_compute_mode_sovereign():
    res = await research_handler.run({}, "nextchapter", {"query": "Test", "compute_mode": "sovereign"})
    assert res["llmContext"]["routing"]["compute_mode"] == "sovereign"


# 13. Compute mode: balanced
@pytest.mark.asyncio
async def test_13_compute_mode_balanced():
    res = await research_handler.run({}, "nextchapter", {"query": "Test", "compute_mode": "balanced"})
    assert res["llmContext"]["routing"]["compute_mode"] == "balanced"


# 14. Anonymity metadata active
@pytest.mark.asyncio
async def test_14_anonymity_metadata_active():
    res = await research_handler.run({}, "nextchapter", {"query": "Test", "anonymize": True})
    assert res["anonymity_active"] is True
    assert res["llmContext"]["routing"]["anonymize"] is True


# 15. Dual retrieval web fallback
@pytest.mark.asyncio
async def test_15_dual_retrieval_web_fallback():
    agent = ResearchAgent(MockAgentContext(), MockMCPAdapter())
    inp = ResearchInput(tenant_id="nextchapter", produced_by="test", query="Unique Uncached Query 98765")
    res = await agent.run(inp)
    assert len(res.sources) > 0


# 16. Dual retrieval local fallback
@pytest.mark.asyncio
async def test_16_dual_retrieval_local_fallback():
    res = await research_handler.run({}, "nextchapter", {"query": "Lokal Test"})
    assert isinstance(res["sources"], list)


# 17. Prompt Inspector context capture
@pytest.mark.asyncio
async def test_17_prompt_inspector_context_capture():
    res = await research_handler.run({}, "nextchapter", {"query": "Prompt Inspection Test"})
    ctx = res["llmContext"]
    assert "prompt" in ctx
    assert "system" in ctx["prompt"]
    assert "user" in ctx["prompt"]
    assert "contextCharCount" in ctx["prompt"]
    assert ctx["prompt"]["contextCharCount"] > 0


# 18. Multi-turn dialogue refinement
@pytest.mark.asyncio
async def test_18_multi_turn_dialogue_refinement():
    refinement = "Fokussiere auf Lizenzkosten und erstelle einen Tabellenvergleich"
    res = await research_handler.run(
        {}, "nextchapter", {"query": "SAP vs Oracle", "refinement_feedback": refinement}
    )
    assert any(refinement in sq for sq in res["sub_questions"])


# 19. DataProduct Pydantic Schema Validation
def test_19_dataproduct_schema_validation():
    inp = ResearchInput(tenant_id="nextchapter", produced_by="unit_test", query="Schema Test")
    assert inp.__class__.__name__ == "ResearchInput"
    assert inp.dp_id.startswith("dp-")
    assert inp.query == "Schema Test"

    res = ResearchResult(
        tenant_id="nextchapter",
        produced_by="unit_test",
        query="Schema Test",
        summary="Zusammenfassung",
        confidence=0.95,
    )
    assert res.__class__.__name__ == "ResearchResult"
    assert res.dp_id.startswith("dp-")
    assert res.confidence == 0.95


# 20. End-to-end Orchestrator Intent Routing & Dispatch Integration
@pytest.mark.asyncio
async def test_20_dispatch_end_to_end_integration():
    intent = route_intent("recherche zu KI-Agenten 2026")
    assert intent == "research"

    res = await dispatch("research", {}, "nextchapter", {"query": "KI-Agenten 2026"})
    assert res["query"] == "KI-Agenten 2026"
    assert "summary" in res
    assert "llmContext" in res
