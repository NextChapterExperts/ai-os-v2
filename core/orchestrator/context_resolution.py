"""Context Bundle stub — 6 slices (P1)."""

from __future__ import annotations

from typing import Any

from .brain_store import active_engagements, list_offerings


def resolve_context(
    intent: str,
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    offerings = list_offerings()
    engagements = active_engagements()
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
        },
        "retrieval": {
            "note": "Unified Search Phase 1 — stub; Memory via capture DB",
            "chunks": [],
        },
        "episodic": {
            "recent_runs": [],
            "note": "Letta episodic later",
        },
        "guardrail": {
            "policies": ["sovereign_default", "sources_on_demand"],
        },
        "skill": {
            "skills": [],
            "note": "Skill-Loop Phase 2",
        },
    }
