"""Audit-Einträge für LLM-Completions in ai_os_log (P17 Hash-Chain)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from core.orchestrator.db import get_connection


def _hash_entry(prev_hash: str | None, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(((prev_hash or "") + canonical).encode("utf-8")).hexdigest()


def write_llm_audit(
    tenant_id: str,
    *,
    model: str,
    produced_by: str,
    session_id: str,
    prompt_preview: str,
    response_preview: str,
    usage: dict[str, Any] | None = None,
    compute_mode: str | None = None,
) -> str:
    """Schreibt llm_completion in ai_os_log; gibt entry_hash zurück."""
    audit_payload = {
        "event": "llm_completion",
        "model": model,
        "produced_by": produced_by,
        "session_id": session_id,
        "compute_mode": compute_mode,
        "prompt_preview": prompt_preview[:400],
        "response_preview": response_preview[:400],
        "usage": usage or {},
    }
    with get_connection() as conn:
        prev = conn.execute(
            "SELECT entry_hash FROM ai_os_log WHERE tenant_id = %s ORDER BY created_at DESC LIMIT 1",
            (tenant_id,),
        ).fetchone()
        prev_hash = prev["entry_hash"] if prev else None
        entry_hash = _hash_entry(prev_hash, audit_payload)
        conn.execute(
            """
            INSERT INTO ai_os_log (tenant_id, event_type, payload, prev_hash, entry_hash)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                tenant_id,
                "llm_completion",
                json.dumps(audit_payload, ensure_ascii=False),
                prev_hash,
                entry_hash,
            ),
        )
    return entry_hash
