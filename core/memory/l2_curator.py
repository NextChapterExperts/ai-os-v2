"""L2-Curator — verdichtet L1-Chunks (24h) zu Tagesdigest-Episoden in Letta Archival.

Pipeline (docs/01-ARCHITEKTUR.md Memory-Flywheel):
  SQLite chunks (24h) → LLM-Tagesdigest → Letta L2 Archival

Standard: gestern (Europe/Berlin), passend zum täglichen Lauf um 02:00.
Einzel-Chunks werden bereits live nach Letta gesynct; L2 erzeugt die
verdichtete Episoden-Zusammenfassung pro Tag.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from core.memory_gateway.audit import write_llm_audit
from core.memory_gateway.client import chat_completion
from core.memory_gateway.letta_client import (
    insert_archival,
    is_available as letta_available,
    list_archival,
)
from core.orchestrator.memory_store import chunks_in_window

log = logging.getLogger("l2_curator")

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "memory-curator.yaml"
STATE_DIR = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory")) / "state"
PROCESSED_STATE = Path(
    os.environ.get("L2_CURATOR_STATE", str(STATE_DIR / "l2-curator-processed.json"))
)

_SUMMARY_SYSTEM = """Du bist der L2-Curator des AI-OS Company Brain.
Erstelle aus den Chat-Chunks eines Tages eine verdichtete Tageszusammenfassung.

Regeln:
- Deutsch, max. 8 Bulletpoints (je eine Zeile, `- ` Prefix)
- Nur große Themen: Entscheidungen, Implementierungen, Blocker, Ergebnisse
- Keine Dateipfade, keine Höflichkeiten, keine Wiederholungen
- Wenn kaum Substanz: genau 1 Bullet „Keine wesentlichen Aktivitäten"
- Kein Markdown außer den Bulletpoints"""


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {
        "l2_min_user_chunks": 3,
        "l2_max_context_chars": 12000,
        "l2_day_offset": -1,
    }


def _cfg(key: str, default: Any) -> Any:
    return _load_config().get(key, default)


def _load_state() -> dict[str, Any]:
    if not PROCESSED_STATE.is_file():
        return {"days": []}
    try:
        return json.loads(PROCESSED_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"days": []}


def _save_state(state: dict[str, Any]) -> None:
    PROCESSED_STATE.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _day_window(offset_days: int) -> tuple[str, str, str]:
    """(start_iso, end_iso, label YYYY-MM-DD) in Europe/Berlin."""
    tz = ZoneInfo("Europe/Berlin")
    now = datetime.now(tz)
    start = (now + timedelta(days=offset_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    label = start.strftime("%Y-%m-%d")
    return (
        start.astimezone(timezone.utc).isoformat(),
        end.astimezone(timezone.utc).isoformat(),
        label,
    )


def _digest_marker(day_label: str) -> str:
    return f"Tagesdigest={day_label}"


def _already_curated(day_label: str, tenant_id: str) -> bool:
    marker = _digest_marker(day_label)
    for row in list_archival(tenant_id, max_items=500):
        text = str(row.get("text") or "")
        if marker in text:
            return True
    return False


def _build_context(chunks: list[dict[str, Any]], max_chars: int) -> str:
    parts: list[str] = []
    used = 0
    for c in chunks:
        role = str(c.get("role") or "user")
        body = str(c.get("body") or "").strip().replace("\n", " ")
        if len(body) < 8:
            continue
        line = f"[{role}] {body[:400]}"
        if used + len(line) > max_chars:
            break
        parts.append(line)
        used += len(line)
    return "\n".join(parts)


async def run_l2_curate(
    tenant_id: str = "nextchapter",
    *,
    day_offset: int | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """L2-Curator — Tages-Chunks zu Letta-Archival-Episode verdichten."""
    if not letta_available():
        return {"ok": False, "error": "letta_unavailable", "tenant_id": tenant_id}

    offset = int(day_offset if day_offset is not None else _cfg("l2_day_offset", -1))
    min_chunks = int(_cfg("l2_min_user_chunks", 3))
    max_chars = int(_cfg("l2_max_context_chars", 12000))

    start, end, day_label = _day_window(offset)
    state = _load_state()
    curated_days: set[str] = set(state.get("days") or [])

    if not force and day_label in curated_days:
        return {
            "ok": True,
            "skipped": "already_in_state",
            "day": day_label,
            "tenant_id": tenant_id,
            "dry_run": dry_run,
        }

    if not force and _already_curated(day_label, tenant_id):
        curated_days.add(day_label)
        state["days"] = sorted(curated_days)[-400:]
        if not dry_run:
            _save_state(state)
        return {
            "ok": True,
            "skipped": "already_in_letta",
            "day": day_label,
            "tenant_id": tenant_id,
            "dry_run": dry_run,
        }

    all_chunks = chunks_in_window(None, start, end, limit=200)
    user_chunks = [c for c in all_chunks if c.get("role") == "user"]
    if len(user_chunks) < min_chunks:
        return {
            "ok": True,
            "skipped": "insufficient_chunks",
            "day": day_label,
            "user_chunks": len(user_chunks),
            "min_required": min_chunks,
            "tenant_id": tenant_id,
            "dry_run": dry_run,
        }

    context = _build_context(user_chunks, max_chars)
    if not context.strip():
        return {
            "ok": True,
            "skipped": "empty_context",
            "day": day_label,
            "tenant_id": tenant_id,
            "dry_run": dry_run,
        }

    result = await chat_completion(
        [
            {"role": "system", "content": _SUMMARY_SYSTEM},
            {
                "role": "user",
                "content": f"Tag: {day_label}\n\nChat-Chunks:\n{context}",
            },
        ],
        tenant_id=tenant_id,
        produced_by="l2-curator",
        max_tokens=500,
        temperature=0.2,
        persist=False,
    )
    summary = (result.get("content") or "").strip()
    if not summary:
        return {"ok": False, "error": "empty_summary", "day": day_label, "tenant_id": tenant_id}

    ts = datetime.strptime(day_label, "%Y-%m-%d").replace(
        hour=23, minute=59, tzinfo=ZoneInfo("Europe/Berlin")
    ).astimezone(timezone.utc)
    when = ts.strftime("%Y-%m-%dT%H:%M")
    summary_flat = summary.replace("\n", " ").replace("|", "/")[:900]
    full_episode = (
        f"[{when}] THEMA: Tagesdigest {day_label} | "
        f"ENTSCHEIDUNG: {_digest_marker(day_label)} | "
        f"OFFEN: chunks={len(user_chunks)} | "
        f"ANTWORT: {summary_flat}"
    )

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "day": day_label,
            "user_chunks": len(user_chunks),
            "episode_preview": full_episode[:300],
            "tenant_id": tenant_id,
        }

    insert_result = insert_archival(tenant_id, full_episode)
    if not insert_result.get("success"):
        return {
            "ok": False,
            "error": insert_result.get("error"),
            "day": day_label,
            "tenant_id": tenant_id,
        }

    audit_hash = write_llm_audit(
        tenant_id,
        model=result.get("model") or "l2-curator",
        produced_by="memory-agent/l2-curator",
        session_id=f"l2-{day_label}",
        prompt_preview=f"Tagesdigest {day_label} ({len(user_chunks)} chunks)",
        response_preview=summary[:200],
        usage={"user_chunks": len(user_chunks), "day": day_label},
    )

    curated_days.add(day_label)
    state["days"] = sorted(curated_days)[-400:]
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_day"] = day_label
    _save_state(state)

    return {
        "ok": True,
        "day": day_label,
        "tenant_id": tenant_id,
        "user_chunks": len(user_chunks),
        "passage_id": insert_result.get("passage_id"),
        "audit_hash": audit_hash,
        "episode_chars": len(full_episode),
        "dry_run": False,
    }
