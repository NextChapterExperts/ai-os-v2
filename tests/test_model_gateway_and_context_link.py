"""Test suite for Local Model Gateway, Context Size Display & CAP Memory Search Regression."""

from __future__ import annotations

import os
import sys
import pytest
from unittest.mock import AsyncMock, patch

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory_gateway.config import model_for_mode, OLLAMA_MODEL
from core.orchestrator.handlers import memory_ask


def test_sovereign_default_model_is_qwen2_5_32b():
    """Verify default sovereign model is set to qwen2.5-coder:32b or qwen2.5:32b."""
    assert OLLAMA_MODEL in ("qwen2.5-coder:32b", "qwen2.5:32b")
    assert model_for_mode("sovereign") == "ai-os-sovereign"


@pytest.mark.asyncio
async def test_memory_ask_cap_query_returns_context_char_count():
    """Verify memory_ask handler includes contextCharCount in result dictionary."""
    mock_llm_res = {
        "content": "• Im Projekt DashBoard-Petru wurde am 08.08.2026 die CAP-Applikation besprochen.",
        "model": "qwen3.6:27b",
    }
    with patch("core.orchestrator.handlers.memory_ask.chat_completion", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_llm_res
        res = await memory_ask.run(
            context_bundle={},
            tenant_id="nextchapter",
            params={"query": "Wo und in welchem Projekt habe ich eine CAP-Applikation besprochen?"},
        )
        assert res.get("kind") == "ask"
        assert "contextCharCount" in res
        assert isinstance(res["contextCharCount"], int)
        assert res["contextCharCount"] >= 0
        assert res.get("runId") is not None


@pytest.mark.asyncio
async def test_memory_ask_federated_keywords_detect_cap_and_dashboard():
    """Verify keywords 'CAP', 'CAP-Applikation', and 'ND Graffiti' trigger federated search."""
    from core.orchestrator.handlers.memory_ask import _needs_federated_context

    assert _needs_federated_context("Wo wurde die CAP-Applikation besprochen?") is True
    assert _needs_federated_context("Stand beim ND Graffiti Dashboard") is True
