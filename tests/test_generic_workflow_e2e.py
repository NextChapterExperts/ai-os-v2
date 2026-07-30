"""Pytest Suite — End-to-End Execution von deterministischen Workflows."""

import os
import sys
import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.workflow_engine.generic_runner import execute_registered_workflow, get_workflow_registry
import core.workflow_engine.sample_workflows  # Register sample workflows


def test_sample_workflow_registration():
    """Prüft ob der Handwerk-Angebot Workflow registriert ist."""
    registry = get_workflow_registry()
    assert "handwerk-angebot" in registry
    wf = registry["handwerk-angebot"]
    assert wf.name == "Handwerk Angebot Erstellung"
    assert "kunden_name" in wf.input_schema.model_json_schema()["properties"]


@pytest.mark.asyncio
async def test_execute_registered_workflow_e2e():
    """Führt den Handwerk-Angebot Workflow end-to-end aus und prüft DataProduct Output."""
    payload = {
        "kunden_name": "Malerbetrieb Schulze",
        "projekt_titel": "Fassadenanstrich",
        "umfang_qm": 100.0,
        "stundensatz": 70.0,
    }
    result = await execute_registered_workflow("handwerk-angebot", "nextchapter", payload)

    assert result["status"] == "completed"
    assert result["workflow_id"] == "handwerk-angebot"

    output_dp = result["output_dp"]
    assert output_dp["kunden_name"] == "Malerbetrieb Schulze"
    assert output_dp["netto_gesamt"] == 4700.0  # (100 * 0.5 * 70) + (100 * 12) = 3500 + 1200 = 4700
    assert output_dp["brutto_gesamt"] == 5593.0 # 4700 * 1.19
    assert "Angebot für Malerbetrieb Schulze" in output_dp["angebot_text"]
