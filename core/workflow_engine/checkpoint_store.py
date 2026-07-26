"""LangGraph Checkpoint Store — Postgres + SQLite Fallback (P7/P15).

Persistiert den Zustand langlaufender Workflows in `workflow_checkpoints` und
ermöglicht das Unterbrechen (`interrupt`) und Wiederaufnehmen (`resume`).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("checkpoint_store")

STATE_DIR = Path(
    os.environ.get("AIOS_STATE_DIR", "/opt/ai-os/memory/state/checkpoints")
)


def _get_file_path(thread_id: str) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    sanitized = "".join(c if c.isalnum() or c in "-_" else "_" for c in thread_id)
    return STATE_DIR / f"{sanitized}.json"


def save_checkpoint(
    thread_id: str,
    checkpoint_id: str,
    state: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Speichert einen Workflow-Zustand in Postgres mit Datei-Fallback."""
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "thread_id": thread_id,
        "checkpoint_id": checkpoint_id,
        "state": state,
        "metadata": metadata or {},
        "created_at": now_iso,
    }

    # 1. Datei-Fallback
    file_path = _get_file_path(thread_id)
    checkpoints = []
    if file_path.exists():
        try:
            checkpoints = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            checkpoints = []

    # Bestehenden Checkpoint aktualisieren oder hinzufügen
    checkpoints = [c for c in checkpoints if c.get("checkpoint_id") != checkpoint_id]
    checkpoints.append(record)
    file_path.write_text(json.dumps(checkpoints, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Versuch, Postgres zu aktualisieren (fails open wenn Postgres offline)
    try:
        from core.orchestrator.db import get_connection

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO workflow_checkpoints (thread_id, checkpoint_id, metadata, created_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (thread_id, checkpoint_id)
                DO UPDATE SET metadata = EXCLUDED.metadata
                """,
                (thread_id, checkpoint_id, json.dumps(metadata or {}, ensure_ascii=False)),
            )
    except Exception as exc:
        log.debug("Postgres Checkpoint-Persistierung übersprungen (Offline-Fallback): %s", exc)

    return record


def load_checkpoint(thread_id: str, checkpoint_id: str | None = None) -> dict[str, Any] | None:
    """Lädt einen spezifischen oder den neuesten Checkpoint eines Threads."""
    file_path = _get_file_path(thread_id)
    if not file_path.exists():
        return None

    try:
        checkpoints: list[dict[str, Any]] = json.loads(file_path.read_text(encoding="utf-8"))
        if not checkpoints:
            return None

        if checkpoint_id:
            for c in checkpoints:
                if c.get("checkpoint_id") == checkpoint_id:
                    return c
            return None

        # Neuesten Checkpoint liefern
        return checkpoints[-1]
    except Exception as exc:
        log.warning("Fehler beim Laden des Checkpoints für %s: %s", thread_id, exc)
        return None


def list_checkpoints(thread_id: str) -> list[dict[str, Any]]:
    """Listet alle bekannten Checkpoints eines Threads."""
    file_path = _get_file_path(thread_id)
    if not file_path.exists():
        return []
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []
