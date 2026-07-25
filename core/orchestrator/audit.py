"""Simple file/JSON audit trail (P9/P17 skeleton — hash-chain later)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(
    __import__("os").environ.get(
        "AIOS_AUDIT_PATH",
        "/opt/ai-os/memory/state/orchestrator-audit.jsonl",
    )
)


def write_agent_run(
    intent: str,
    result: dict[str, Any],
    tenant_id: str,
    *,
    extra: dict[str, Any] | None = None,
) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tenant_id": tenant_id,
        "intent": intent,
        "kind": result.get("kind"),
        "answer_preview": str(result.get("answer", ""))[:240],
        "sourceCount": result.get("sourceCount", 0),
    }
    if extra:
        entry.update(extra)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
