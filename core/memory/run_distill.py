"""Run-Ende-Destillation — Working/Tactical → Letta L2 oder Audit-only (P9).

Nie still verwerfen: leerer Run → audit-only discard mit Begründung.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.memory.tactical_memory import close_workflow, delete_workflow, get_snapshot as get_tactical
from core.memory.working_memory import append_note, close_run, delete_run, get_snapshot as get_working
from core.memory_gateway.letta_client import insert_archival, is_available as letta_available

log = logging.getLogger("run_distill")

AUDIT_PATH = Path(
    os.environ.get(
        "AIOS_AUDIT_PATH",
        "/opt/ai-os/memory/state/orchestrator-audit.jsonl",
    )
)

MIN_NOTES_FOR_LETTA = int(os.environ.get("RUN_DISTILL_MIN_NOTES", "1"))


def _format_distill_text(
    intent: str,
    working: dict[str, Any] | None,
    tactical: dict[str, Any] | None,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    lines = [f"[{ts}] Run-Destillation intent={intent}"]

    if working and working.get("notes"):
        lines.append("Working:")
        for n in working["notes"][-12:]:
            lines.append(f"- ({n.get('kind', 'note')}) {n.get('text', '')[:300]}")

    if tactical and tactical.get("steps"):
        lines.append("Tactical:")
        for s in tactical["steps"][-8:]:
            lines.append(f"- Schritt {s.get('step')}: {s.get('label')} — {s.get('result_preview', '')[:200]}")

    return "\n".join(lines)


def _write_distill_audit(entry: dict[str, Any]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def distill_after_run(
    tenant_id: str,
    run_id: str,
    workflow_run_id: str | None,
    intent: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Destilliert Working/Tactical am Run-Ende nach L2 oder Audit-only."""
    working = get_working(run_id)
    tactical = get_tactical(workflow_run_id) if workflow_run_id else None

    note_count = len(working.get("notes", [])) if working else 0
    step_count = len(tactical.get("steps", [])) if tactical else 0
    has_substance = note_count >= MIN_NOTES_FOR_LETTA or step_count > 0

    outcome: dict[str, Any] = {
        "run_id": run_id,
        "workflow_run_id": workflow_run_id,
        "intent": intent,
        "working_notes": note_count,
        "tactical_steps": step_count,
        "action": "discard_audit",
        "letta": None,
    }

    if has_substance:
        text = _format_distill_text(intent, working, tactical)
        if letta_available():
            letta_result = insert_archival(tenant_id, text)
            outcome["letta"] = letta_result
            outcome["action"] = "letta_archival" if letta_result.get("success") else "letta_failed_audit"
        else:
            outcome["action"] = "letta_unavailable_audit"
            append_note(run_id, f"[distill-fallback] {text[:400]}", kind="distill_fallback")

    close_run(run_id)
    if workflow_run_id:
        close_workflow(workflow_run_id)

    _write_distill_audit(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "run_distill",
            "tenant_id": tenant_id,
            **outcome,
            "answer_preview": str(result.get("answer", ""))[:240],
        }
    )

    delete_run(run_id)
    if workflow_run_id:
        delete_workflow(workflow_run_id)

    log.info(
        "Run-Destillation %s: action=%s notes=%d steps=%d",
        run_id,
        outcome["action"],
        note_count,
        step_count,
    )
    return outcome
