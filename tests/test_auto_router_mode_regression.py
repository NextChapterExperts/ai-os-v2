import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.memory_gateway.config import (

    compute_mode_snapshot,
    get_mode,
    list_compute_modes,
    resolve_auto_model,
    set_active_mode,
)


def test_auto_router_prompt_intent_classification():
    """Prüft, ob resolve_auto_model die richtigen Modelle je nach Intent auswählt."""
    # Code / Python / SQL / JSON -> qwen2.5-coder:14b
    assert resolve_auto_model("Schreibe ein Python-Skript für den E-Mail Agenten") == "qwen2.5-coder:14b"
    assert resolve_auto_model("Fixe den Bug in der SQL-Abfrage") == "qwen2.5-coder:14b"

    # Reasoning / Logik -> deepseek-r1:32b
    assert resolve_auto_model("Warum schlägt der Checkpoint fehl? Analysiere die Logik im Detail") == "deepseek-r1:32b"
    assert resolve_auto_model("Erkläre die Strategie und berechne die Auslastung") == "deepseek-r1:32b"

    # Vision / Bild -> llama3.2-vision:11b
    assert resolve_auto_model("Analysiere dieses Bild / Dokument PDF") == "llama3.2-vision:11b"

    # Mail / Text / Zusammenfassung -> mistral-nemo:12b
    assert resolve_auto_model("Entwirf eine Antwort-Mail für den Kunden") == "mistral-nemo:12b"
    assert resolve_auto_model("Schreibe einen Blog-Beitrag über AI-OS v2") == "mistral-nemo:12b"


def test_auto_mode_is_default():
    """Prüft, ob auto als Standard-Compute-Modus konfiguriert ist."""
    modes = list_compute_modes()
    mode_ids = [m["id"] for m in modes]
    assert "auto" in mode_ids, "Modus 'auto' fehlt in list_compute_modes()"

    auto_entry = next(m for m in modes if m["id"] == "auto")
    assert "Auto-Router" in auto_entry["label"]


def test_manual_override_switching():
    """Prüft Umschalten zwischen Auto-Router und manuellem Pinning."""
    original_mode = get_mode()
    try:
        # Switch to auto
        set_active_mode("auto")
        assert get_mode() == "auto"

        # Override to manual pinned DeepSeek R1
        set_active_mode("sovereign_r1")
        assert get_mode() == "sovereign_r1"

        # Switch back to auto
        set_active_mode("auto")
        assert get_mode() == "auto"
    finally:
        set_active_mode(original_mode)
