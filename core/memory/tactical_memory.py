"""Tactical Memory — Multi-Step-Workflow-Zwischenstand (flüchtig, P9).

State-Dateien unter `{AIOS_MEMORY_ROOT}/state/tactical/{workflow_run_id}.json`.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory")) / "state" / "tactical"


def _path(workflow_run_id: str) -> Path:
    safe = workflow_run_id.replace("/", "_").replace("..", "_")
    return STATE_DIR / f"{safe}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_workflow(
    workflow_run_id: str,
    tenant_id: str,
    *,
    name: str | None = None,
) -> dict[str, Any]:
    """Öffnet oder lädt einen Tactical-Workflow."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(workflow_run_id)
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if name and not data.get("name"):
                data["name"] = name
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data
        except json.JSONDecodeError:
            pass

    data = {
        "workflow_run_id": workflow_run_id,
        "tenant_id": tenant_id,
        "name": name,
        "opened_at": _now(),
        "steps": [],
        "closed": False,
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def record_step(
    workflow_run_id: str,
    step: int,
    label: str,
    result_preview: str,
    *,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Zeichnet einen Workflow-Schritt auf."""
    p = _path(workflow_run_id)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("closed"):
        return data

    entry: dict[str, Any] = {
        "step": step,
        "label": label,
        "result_preview": result_preview[:800],
        "ts": _now(),
    }
    if meta:
        entry["meta"] = meta
    data.setdefault("steps", []).append(entry)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def record_from_params(workflow_run_id: str, params: dict[str, Any], result: dict[str, Any]) -> None:
    """Optional: Schritt aus params.step / params.step_label."""
    step = params.get("step")
    label = params.get("step_label") or params.get("workflow_step")
    if step is None and label is None:
        return
    preview = str(result.get("answer") or "")[:400]
    record_step(
        workflow_run_id,
        int(step) if step is not None else len(get_snapshot(workflow_run_id) or {"steps": []}) + 1,
        str(label or f"step-{step}"),
        preview,
    )


def get_snapshot(workflow_run_id: str) -> dict[str, Any] | None:
    p = _path(workflow_run_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def close_workflow(workflow_run_id: str) -> dict[str, Any] | None:
    p = _path(workflow_run_id)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    data["closed"] = True
    data["closed_at"] = _now()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def delete_workflow(workflow_run_id: str) -> bool:
    p = _path(workflow_run_id)
    if p.is_file():
        p.unlink()
        return True
    return False
