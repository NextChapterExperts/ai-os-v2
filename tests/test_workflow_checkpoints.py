"""Unit tests for LangGraph Checkpointing, Interrupt, and Resume."""

from __future__ import annotations

import os
import sys
from fastapi.testclient import TestClient

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.server import app
from core.workflow_engine.checkpoint_store import list_checkpoints, load_checkpoint, save_checkpoint
from core.workflow_engine.engine import interrupt_workflow, resume_workflow

client = TestClient(app)


def test_checkpoint_store_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr("core.workflow_engine.checkpoint_store.STATE_DIR", tmp_path / "checkpoints")
    thread_id = "thread-test-001"

    rec1 = save_checkpoint(thread_id, "ckpt-1", {"step": 1, "data": "initial"}, {"node": "planner"})
    assert rec1["checkpoint_id"] == "ckpt-1"

    rec2 = save_checkpoint(thread_id, "ckpt-2", {"step": 2, "data": "updated"}, {"node": "executor"})
    assert rec2["checkpoint_id"] == "ckpt-2"

    latest = load_checkpoint(thread_id)
    assert latest is not None
    assert latest["checkpoint_id"] == "ckpt-2"
    assert latest["state"]["step"] == 2

    specific = load_checkpoint(thread_id, "ckpt-1")
    assert specific is not None
    assert specific["checkpoint_id"] == "ckpt-1"

    all_ckpts = list_checkpoints(thread_id)
    assert len(all_ckpts) == 2


def test_interrupt_and_resume_flow(tmp_path, monkeypatch):
    monkeypatch.setattr("core.workflow_engine.checkpoint_store.STATE_DIR", tmp_path / "checkpoints")
    thread_id = "thread-flow-002"

    int_res = interrupt_workflow(thread_id, reason="Human-in-the-loop approval needed", pending_state={"action": "deploy"})
    assert int_res["status"] == "interrupted"
    assert int_res["reason"] == "Human-in-the-loop approval needed"

    ckpt = load_checkpoint(thread_id)
    assert ckpt is not None
    assert ckpt["state"]["status"] == "interrupted"

    res_res = resume_workflow(thread_id, input_data={"approved": True})
    assert res_res["status"] == "resumed"
    assert res_res["state"]["status"] == "active"
    assert res_res["state"]["resumed_with"]["approved"] is True


def test_workflow_checkpoint_and_resume_api(tmp_path, monkeypatch):
    monkeypatch.setattr("core.workflow_engine.checkpoint_store.STATE_DIR", tmp_path / "checkpoints")
    thread_id = "thread-api-003"

    save_checkpoint(thread_id, "ckpt-api-1", {"step": "pending_approval"})

    res_get = client.get(f"/v1/workflow/checkpoint/{thread_id}")
    assert res_get.status_code == 200
    assert res_get.json()["checkpoint_id"] == "ckpt-api-1"

    res_post = client.post("/v1/workflow/resume", json={"thread_id": thread_id, "input_data": {"user_decision": "ok"}})
    assert res_post.status_code == 200
    assert res_post.json()["status"] == "resumed"
