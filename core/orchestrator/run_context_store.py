"""Persist LLM prompt context per orchestrator run (audit / governance)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONTEXT_DIR = Path(
    os.environ.get(
        "AIOS_RUN_CONTEXT_DIR",
        "/opt/ai-os/memory/state/run-context",
    )
)


def save_run_context(run_id: str, context: dict[str, Any]) -> None:
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTEXT_DIR / f"{run_id}.json"
    path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")


def load_run_context(run_id: str) -> dict[str, Any] | None:
    path = CONTEXT_DIR / f"{run_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
