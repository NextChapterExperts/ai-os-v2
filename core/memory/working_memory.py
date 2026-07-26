"""Working Memory — flüchtiger Task-Scratchpad pro Run (P9 Destillation).

State-Dateien unter `{AIOS_MEMORY_ROOT}/state/working/{run_id}.json`.
LangGraph-Checkpoints später; vorerst file-based.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import re

STATE_DIR = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory")).resolve() / "state" / "working"


def _path(run_id: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", run_id)
    p = (STATE_DIR / f"{safe}.json").resolve()
    if not str(p).startswith(str(STATE_DIR)):
        raise ValueError(f"Invalid run_id: {run_id}")
    return p


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_run(
    run_id: str,
    tenant_id: str,
    *,
    intent: str | None = None,
) -> dict[str, Any]:
    """Öffnet oder lädt einen Working-Memory-Run."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(run_id)
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if intent and not data.get("intent"):
                data["intent"] = intent
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data
        except json.JSONDecodeError:
            pass

    data = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "intent": intent,
        "opened_at": _now(),
        "notes": [],
        "closed": False,
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def append_note(
    run_id: str,
    text: str,
    *,
    kind: str = "scratch",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Fügt eine Notiz zum Working-Memory hinzu."""
    p = _path(run_id)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("closed"):
        return data

    entry: dict[str, Any] = {"ts": _now(), "text": text.strip(), "kind": kind}
    if meta:
        entry["meta"] = meta
    data.setdefault("notes", []).append(entry)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def append_from_dispatch(run_id: str, intent: str, result: dict[str, Any]) -> None:
    """Nach Dispatch: Antwort-Vorschau als Working-Notiz."""
    preview = str(result.get("answer") or "")[:500]
    if not preview:
        return
    append_note(
        run_id,
        preview,
        kind="dispatch_result",
        meta={"intent": intent, "kind": result.get("kind"), "sourceCount": result.get("sourceCount")},
    )


def get_snapshot(run_id: str) -> dict[str, Any] | None:
    """Liefert Working-Memory für Context-Bundle."""
    p = _path(run_id)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def close_run(run_id: str) -> dict[str, Any] | None:
    """Schließt Run (Datei bleibt bis Destillation)."""
    p = _path(run_id)
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


def delete_run(run_id: str) -> bool:
    """Entfernt State-Datei nach Destillation."""
    p = _path(run_id)
    if p.is_file():
        p.unlink()
        return True
    return False
