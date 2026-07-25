"""LangFuse-Trace nach LLM-Completion (optional, Phase 1 Pflicht-Hook)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

log = logging.getLogger("memory_gateway.langfuse")

LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "http://127.0.0.1:3000")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")


def trace_llm_completion(
    *,
    tenant_id: str,
    model: str,
    produced_by: str,
    session_id: str,
    prompt_preview: str,
    response_preview: str,
    usage: dict[str, Any] | None = None,
) -> bool:
    """Sendet einen minimalen Trace an LangFuse. Gibt False zurück wenn nicht konfiguriert."""
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        return False

    host = LANGFUSE_HOST.rstrip("/")
    if host.startswith("http://langfuse:"):
        host = "http://127.0.0.1:3000"

    payload = {
        "batch": [
            {
                "id": f"mg-{session_id}",
                "type": "trace-create",
                "timestamp": None,
                "body": {
                    "id": session_id,
                    "name": f"memory-gateway/{produced_by}",
                    "userId": tenant_id,
                    "metadata": {"model": model, "produced_by": produced_by},
                },
            },
            {
                "id": f"mg-gen-{session_id}",
                "type": "generation-create",
                "timestamp": None,
                "body": {
                    "traceId": session_id,
                    "name": produced_by,
                    "model": model,
                    "input": prompt_preview[:500],
                    "output": response_preview[:500],
                    "usage": usage or {},
                },
            },
        ]
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.post(
                f"{host}/api/public/ingestion",
                json=payload,
                auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY),
            )
            if res.status_code >= 400:
                log.warning("LangFuse ingestion %s: %s", res.status_code, res.text[:200])
                return False
            return True
    except Exception:
        log.exception("LangFuse trace fehlgeschlagen")
        return False
