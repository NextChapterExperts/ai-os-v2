"""Regression test suite for local Monster server models & compute modes."""

import pytest
from core.memory_gateway.config import (
    MODE_TO_OLLAMA_MODEL,
    compute_mode_snapshot,
    get_mode,
    list_compute_modes,
    model_for_mode,
    set_active_mode,
)


def test_local_monster_modes_configuration():
    """Prüft, ob alle lokalen Monster-Server Modelle aus api-access zum Monster.md verfügbar sind."""
    modes = list_compute_modes()
    mode_ids = [m["id"] for m in modes]

    expected_local_modes = [
        "sovereign",
        "sovereign_r1",
        "sovereign_coder",
        "sovereign_nemo",
        "sovereign_hermes",
        "sovereign_vision",
        "sovereign_vllm",
    ]

    for expected in expected_local_modes:
        assert expected in mode_ids, f"Modus {expected} fehlt in list_compute_modes()"


def test_monster_mode_to_ollama_mapping():
    """Prüft, ob die Sovereign-Modi korrekt auf die Ollama-Modellnamen mappen."""
    assert MODE_TO_OLLAMA_MODEL["sovereign"] == "qwen2.5-coder:32b"
    assert MODE_TO_OLLAMA_MODEL["sovereign_r1"] == "deepseek-r1:32b"
    assert MODE_TO_OLLAMA_MODEL["sovereign_coder"] == "qwen2.5-coder:32b"
    assert MODE_TO_OLLAMA_MODEL["sovereign_nemo"] == "mistral-nemo:12b"
    assert MODE_TO_OLLAMA_MODEL["sovereign_hermes"] == "hermes3:8b"
    assert MODE_TO_OLLAMA_MODEL["sovereign_vision"] == "llama3.2-vision:11b"


def test_monster_mode_switching():
    """Prüft den Umschalt-Mechanismus für lokale Monster-Modelle."""
    original_mode = get_mode()
    try:
        set_active_mode("sovereign_r1")
        assert get_mode() == "sovereign_r1"
        assert model_for_mode("sovereign_r1") == "ai-os-deepseek-r1"

        set_active_mode("sovereign_nemo")
        assert get_mode() == "sovereign_nemo"
        assert model_for_mode("sovereign_nemo") == "ai-os-mistral-nemo"

        set_active_mode("sovereign_hermes")
        assert get_mode() == "sovereign_hermes"
        assert model_for_mode("sovereign_hermes") == "ai-os-hermes3"

        snap = compute_mode_snapshot()
        assert snap["active_mode"] == "sovereign_hermes"
    finally:
        set_active_mode(original_mode)


def test_vllm_mode_configuration():
    """Prüft die vLLM Konfiguration und den Modellnamen."""
    from core.memory_gateway.config import VLLM_HOST, VLLM_MODEL, VLLM_PORT, vllm_chat_url
    assert VLLM_HOST == "192.168.178.116"
    assert VLLM_PORT == "8001"
    assert VLLM_MODEL == "/workspace/model"
    assert vllm_chat_url() == "http://192.168.178.116:8001/v1/chat/completions"


def test_ollama_monster_host_configuration():
    """Prüft, ob der OLLAMA_HOST auf den aktiven KI-Server (192.168.178.116) zeigt."""
    from core.memory_gateway.config import OLLAMA_HOST, OLLAMA_PORT, ollama_chat_url
    assert OLLAMA_HOST == "192.168.178.116"
    assert OLLAMA_PORT == "11434"
    assert ollama_chat_url() == "http://192.168.178.116:11434/api/chat"


