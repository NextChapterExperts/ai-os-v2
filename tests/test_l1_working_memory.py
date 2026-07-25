"""L1-Curator + Working/Tactical Memory Tests."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.memory.l1_curator import _text_hash, scan_stats
from core.memory import working_memory, tactical_memory, run_distill


def test_text_hash_stable():
    assert _text_hash("hello") == _text_hash("hello")
    assert _text_hash("hello") != _text_hash("world")


def test_scan_stats_missing_collection(monkeypatch):
    class FakeClient:
        def get_collections(self):
            class R:
                collections = []

            return R()

    from core.memory import l1_curator

    monkeypatch.setattr(l1_curator, "_get_client", lambda: FakeClient())
    stats = scan_stats()
    assert stats["exists"] is False
    assert stats["total_points"] == 0


def test_working_memory_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(working_memory, "STATE_DIR", tmp_path)
    data = working_memory.ensure_run("run-1", "nextchapter", intent="ping")
    assert data["run_id"] == "run-1"
    working_memory.append_note("run-1", "Test-Notiz", kind="test")
    snap = working_memory.get_snapshot("run-1")
    assert snap is not None
    assert len(snap["notes"]) == 1
    working_memory.close_run("run-1")
    assert working_memory.delete_run("run-1")


def test_tactical_memory_steps(monkeypatch, tmp_path):
    monkeypatch.setattr(tactical_memory, "STATE_DIR", tmp_path)
    tactical_memory.ensure_workflow("wf-1", "nextchapter", name="test-flow")
    tactical_memory.record_step("wf-1", 1, "fetch", "ok")
    snap = tactical_memory.get_snapshot("wf-1")
    assert snap is not None
    assert len(snap["steps"]) == 1


def test_distill_empty_run_audit_only(monkeypatch, tmp_path):
    monkeypatch.setattr(working_memory, "STATE_DIR", tmp_path / "working")
    monkeypatch.setattr(run_distill, "AUDIT_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(run_distill, "letta_available", lambda: False)

    working_memory.ensure_run("run-empty", "nextchapter", intent="ping")
    outcome = run_distill.distill_after_run("nextchapter", "run-empty", None, "ping", {"answer": "pong"})
    assert outcome["action"] == "discard_audit"
    assert working_memory.get_snapshot("run-empty") is None
    audit_lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(audit_lines) == 1
    entry = json.loads(audit_lines[0])
    assert entry["event"] == "run_distill"
