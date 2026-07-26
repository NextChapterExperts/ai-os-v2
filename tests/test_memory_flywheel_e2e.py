"""End-to-End Memory Flywheel Tests (Working -> Tactical -> Distill -> L2 -> L3)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory import l1_curator, l2_curator, l3_curator, run_distill, storage_stats, tactical_memory, working_memory


def test_working_memory_full_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(working_memory, "STATE_DIR", tmp_path / "working")
    run_id = "test-run-e2e-001"
    tenant_id = "nextchapter"

    # 1. Ensure run
    run_data = working_memory.ensure_run(run_id, tenant_id, intent="memory_ask")
    assert run_data["run_id"] == run_id
    assert run_data["intent"] == "memory_ask"
    assert run_data["closed"] is False

    # 2. Append notes
    working_memory.append_note(run_id, "User asked about Company Brain architecture.", kind="user_input")
    working_memory.append_note(run_id, "Brain architecture uses Postgres + Qdrant.", kind="dispatch_result")

    # 3. Check snapshot
    snap = working_memory.get_snapshot(run_id)
    assert snap is not None
    assert len(snap["notes"]) == 2
    assert snap["notes"][0]["text"] == "User asked about Company Brain architecture."

    # 4. Close & Delete
    closed = working_memory.close_run(run_id)
    assert closed["closed"] is True
    assert working_memory.delete_run(run_id) is True
    assert working_memory.get_snapshot(run_id) is None


def test_tactical_memory_full_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(tactical_memory, "STATE_DIR", tmp_path / "tactical")
    wf_id = "wf-e2e-001"
    tenant_id = "nextchapter"

    # 1. Ensure workflow
    wf_data = tactical_memory.ensure_workflow(wf_id, tenant_id, name="multi-step-search")
    assert wf_data["workflow_run_id"] == wf_id
    assert wf_data["name"] == "multi-step-search"

    # 2. Record steps
    tactical_memory.record_step(wf_id, 1, "fetch_graph", "Found 3 nodes in Knowledge Graph")
    tactical_memory.record_step(wf_id, 2, "query_l1", "Found 5 chunks in Qdrant content")

    # 3. Snapshot
    snap = tactical_memory.get_snapshot(wf_id)
    assert snap is not None
    assert len(snap["steps"]) == 2
    assert snap["steps"][0]["label"] == "fetch_graph"

    # 4. Close & Delete
    closed = tactical_memory.close_workflow(wf_id)
    assert closed["closed"] is True
    assert tactical_memory.delete_workflow(wf_id) is True


def test_run_distillation_fallback_and_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(working_memory, "STATE_DIR", tmp_path / "working")
    monkeypatch.setattr(tactical_memory, "STATE_DIR", tmp_path / "tactical")
    monkeypatch.setattr(run_distill, "AUDIT_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(run_distill, "letta_available", lambda: False)

    run_id = "distill-run-001"
    wf_id = "distill-wf-001"
    tenant_id = "nextchapter"

    working_memory.ensure_run(run_id, tenant_id, intent="unified_search")
    working_memory.append_note(run_id, "Crucial search query note", kind="scratch")
    tactical_memory.ensure_workflow(wf_id, tenant_id, name="search_flow")
    tactical_memory.record_step(wf_id, 1, "step_one", "result_preview")

    outcome = run_distill.distill_after_run(
        tenant_id, run_id, wf_id, "unified_search", {"answer": "Search completed"}
    )
    assert outcome["action"] in {"letta_unavailable_audit", "discard_audit"}
    assert outcome["working_notes"] == 1
    assert outcome["tactical_steps"] == 1

    # Verify audit file atomic write
    audit_file = tmp_path / "audit.jsonl"
    assert audit_file.is_file()
    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    audit_data = json.loads(lines[0])
    assert audit_data["event"] == "run_distill"
    assert audit_data["run_id"] == run_id


def test_l2_curator_helpers():
    start, end, label = l2_curator._day_window(-1)
    assert start < end
    assert len(label) == 10  # YYYY-MM-DD

    marker = l2_curator._digest_marker("2026-07-26")
    assert marker == "Tagesdigest=2026-07-26"

    chunks = [{"role": "user", "body": "chunk content " * 10} for _ in range(20)]
    ctx = l2_curator._build_context(chunks, max_chars=500)
    assert len(ctx) <= 600


def test_l3_curator_helpers():
    claim_id = l3_curator._claim_id("AI-OS Company Brain SSOT Rule")
    assert claim_id.startswith("claim-")
    assert claim_id == l3_curator._claim_id("AI-OS Company Brain SSOT Rule")

    raw_response = """
    Here are the extracted facts:
    {
      "claims": [
        {"text": "Postgres Graph is the SSOT for nodes", "confidence": 0.9, "supports_refs": []}
      ],
      "profile_facts": [
        {"key": "role", "value": "AI Platform Lead", "confidence": 0.95}
      ]
    }
    End of response.
    """
    extracted = l3_curator._parse_extraction(raw_response)
    assert len(extracted["claims"]) == 1
    assert extracted["claims"][0]["confidence"] == 0.9
    assert len(extracted["profile_facts"]) == 1
    assert extracted["profile_facts"][0]["key"] == "role"


def test_storage_stats_helper_functions():
    assert storage_stats._fmt(500) == "500 B"
    assert storage_stats._fmt(2048) == "2.0 KB"
    assert storage_stats._fmt(5 * 1024 * 1024) == "5.0 MB"
    assert storage_stats._fmt(3 * 1024 * 1024 * 1024) == "3.00 GB"

    ts = storage_stats._now_iso()
    assert "T" in ts
