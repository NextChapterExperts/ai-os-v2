"""Context Bundle — 6 slices (P1) + Working/Tactical."""

from __future__ import annotations

from typing import Any

from core.memory.tactical_memory import get_snapshot as get_tactical_snapshot
from core.memory.working_memory import get_snapshot as get_working_snapshot

from .brain_store import active_engagements, list_offerings


def resolve_context(
    intent: str,
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    offerings = list_offerings()
    engagements = active_engagements()
    run_id = params.get("run_id") or params.get("session_id")
    workflow_run_id = params.get("workflow_run_id")
    working = get_working_snapshot(str(run_id)) if run_id else None
    tactical = get_tactical_snapshot(str(workflow_run_id)) if workflow_run_id else None
    return {
        "system": {
            "tenant": tenant_id,
            "compute_mode": "sovereign",
            "policies": ["pii_local_default", "no_raw_chat_as_decision"],
        },
        "domain": {
            "offerings": [
                {"id": o["id"], "name": o["name"], "kind": o["kind"]}
                for o in offerings
            ],
            "engagements": [
                {
                    "id": e["id"],
                    "title": e["title"],
                    "status": e["status"],
                    "offering_id": e.get("offering_id"),
                }
                for e in engagements
            ],
        },
        "task": {
            "intent": intent,
            "params": params,
            "input_refs": params.get("input_dp_refs", []),
            "run_id": run_id,
            "workflow_run_id": workflow_run_id,
            "working": working or {"notes": [], "note": "Kein aktiver Run"},
            "tactical": tactical or {"steps": [], "note": "Kein aktiver Workflow"},
        },
        "retrieval": {
            "note": "Unified Search — Graph + L1 Qdrant + episodisch (Letta/SQLite)",
            "chunks": [],
        },
        "episodic": {
            "recent_runs": [],
            "note": "L2 Letta Archival via memory_ask / unified_search / Run-Destillation",
        },
        "guardrail": {
            "policies": ["sovereign_default", "sources_on_demand"],
        },
        "skill": {
            "skills": [],
            "note": "Skill-Loop Phase 2",
        },
    }
