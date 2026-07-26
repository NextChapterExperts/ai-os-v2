"""LangGraph Workflow Engine Runner (P7 State-Machine & Checkpointing)."""

from __future__ import annotations

import uuid
from typing import Any

from .checkpoint_store import load_checkpoint, save_checkpoint


def interrupt_workflow(
    thread_id: str,
    reason: str,
    pending_state: dict[str, Any],
) -> dict[str, Any]:
    """Unterbricht einen Workflow (Human-in-the-Loop Gate) und speichert den Status."""
    checkpoint_id = f"ckpt-interrupt-{uuid.uuid4().hex[:8]}"
    state = {
        "status": "interrupted",
        "interrupt_reason": reason,
        "pending_state": pending_state,
    }
    metadata = {"interrupted": True, "reason": reason}
    record = save_checkpoint(thread_id, checkpoint_id, state, metadata)
    return {
        "status": "interrupted",
        "thread_id": thread_id,
        "checkpoint_id": checkpoint_id,
        "reason": reason,
        "record": record,
    }


def resume_workflow(
    thread_id: str,
    input_data: dict[str, Any],
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    """Nimmt einen unterbrochenen Workflow wieder auf."""
    last_ckpt = load_checkpoint(thread_id, checkpoint_id)
    if not last_ckpt:
        return {
            "status": "error",
            "message": f"Kein gültiger Checkpoint für thread_id={thread_id} gefunden.",
        }

    current_state = last_ckpt.get("state", {})
    new_checkpoint_id = f"ckpt-resumed-{uuid.uuid4().hex[:8]}"

    updated_state = {
        **current_state,
        "status": "active",
        "resumed_with": input_data,
    }
    metadata = {"resumed": True, "previous_checkpoint": last_ckpt.get("checkpoint_id")}

    record = save_checkpoint(thread_id, new_checkpoint_id, updated_state, metadata)
    return {
        "status": "resumed",
        "thread_id": thread_id,
        "checkpoint_id": new_checkpoint_id,
        "state": updated_state,
        "record": record,
    }
