"""Context Bundle — 6 Slices (P1/P13) + Async Parallel Resolution & Caching."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from core.memory.tactical_memory import get_snapshot as get_tactical_snapshot
from core.memory.working_memory import get_snapshot as get_working_snapshot

from .brain_store import active_engagements, list_offerings
from .enterprise_profile_store import get_enterprise_profile
from .kg_search import search_nodes

_CACHE_TTL_SEC = 15
_DOMAIN_CACHE: dict[str, Any] = {"ts": 0.0, "offerings": [], "engagements": []}


def _get_cached_domain() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    now = time.time()
    if now - _DOMAIN_CACHE["ts"] < _CACHE_TTL_SEC and _DOMAIN_CACHE["offerings"]:
        return _DOMAIN_CACHE["offerings"], _DOMAIN_CACHE["engagements"]

    try:
        offerings = list_offerings()
        engagements = active_engagements()
    except Exception:
        offerings = []
        engagements = []

    _DOMAIN_CACHE["offerings"] = offerings
    _DOMAIN_CACHE["engagements"] = engagements
    _DOMAIN_CACHE["ts"] = now
    return offerings, engagements


async def _resolve_retrieval_slice(tenant_id: str, query: str) -> dict[str, Any]:
    if not query:
        return {"note": "Unified Search — Graph + Qdrant", "hits": [], "kg_nodes": []}
    try:
        nodes = await asyncio.to_thread(search_nodes, tenant_id, query, limit=5)
        return {
            "note": "Unified Search — Graph + Qdrant",
            "hits": [
                {
                    "node_id": n.get("id"),
                    "title": n.get("title"),
                    "node_type": n.get("node_type"),
                    "snippet": n.get("snippet"),
                }
                for n in nodes
            ],
            "kg_nodes": nodes,
        }
    except Exception:
        return {"note": "Search unavailable", "hits": [], "kg_nodes": []}


async def _resolve_memory_slice(run_id: str | None, wf_id: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    working_task = asyncio.to_thread(get_working_snapshot, str(run_id)) if run_id else None
    tactical_task = asyncio.to_thread(get_tactical_snapshot, str(wf_id)) if wf_id else None

    working = await working_task if working_task else None
    tactical = await tactical_task if tactical_task else None
    return working or {"notes": [], "note": "Kein aktiver Run"}, tactical or {"steps": [], "note": "Kein aktiver Workflow"}


async def resolve_context_async(
    intent: str,
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Löst alle 6 Slices des Context Bundles asynchron und parallel unter 50ms auf."""
    start_time = time.perf_counter()
    run_id = params.get("run_id") or params.get("session_id")
    workflow_run_id = params.get("workflow_run_id")
    query = str(params.get("query") or params.get("q") or intent)

    user_id = str(params.get("user_id") or "default_user")

    # Parallel Execution: Domain Cache + Memory Snapshots + Retrieval
    domain_task = asyncio.to_thread(_get_cached_domain)
    memory_task = _resolve_memory_slice(run_id, workflow_run_id)
    retrieval_task = _resolve_retrieval_slice(tenant_id, query)

    (offerings, engagements), (working, tactical), retrieval = await asyncio.gather(
        domain_task, memory_task, retrieval_task
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "system": {
            "tenant": tenant_id,
            "user_id": user_id,
            "compute_mode": params.get("compute_mode", "sovereign"),
            "policies": ["pii_local_default", "no_raw_chat_as_decision"],
            "resolution_time_ms": round(elapsed_ms, 2),
        },
        "domain": {
            "offerings": [
                {"id": o["id"], "name": o["name"], "kind": o["kind"]} for o in offerings
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
            "working": working,
            "tactical": tactical,
        },
        "retrieval": retrieval,
        "episodic": {
            "recent_runs": [],
            "note": "L2 Letta Archival via memory_ask / unified_search / Run-Destillation",
        },
        "guardrail": {
            "policies": ["sovereign_default", "sources_on_demand", "pii_auto_redact_on_cloud"],
        },
        "skill": {
            "skills": [],
            "note": "Skill-Loop Phase 2",
        },
        "enterprise": get_enterprise_profile(tenant_id).model_dump(mode="json"),
    }


def resolve_context(
    intent: str,
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Synchrone Hülle für Rückwärtskompatibilität."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Falls bereits im Async Event Loop (z.B. FastAPI): direkt synchronen Fallback ausführen
        offerings, engagements = _get_cached_domain()
        run_id = params.get("run_id") or params.get("session_id")
        workflow_run_id = params.get("workflow_run_id")
        working = get_working_snapshot(str(run_id)) if run_id else None
        tactical = get_tactical_snapshot(str(workflow_run_id)) if workflow_run_id else None
        return {
            "system": {
                "tenant": tenant_id,
                "compute_mode": params.get("compute_mode", "sovereign"),
                "policies": ["pii_local_default", "no_raw_chat_as_decision"],
            },
            "domain": {
                "offerings": [{"id": o["id"], "name": o["name"], "kind": o["kind"]} for o in offerings],
                "engagements": [{"id": e["id"], "title": e["title"], "status": e["status"], "offering_id": e.get("offering_id")} for e in engagements],
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
            "retrieval": {"note": "Unified Search — Graph + Qdrant", "hits": []},
            "episodic": {"recent_runs": [], "note": "L2 Letta Archival"},
            "guardrail": {"policies": ["sovereign_default", "sources_on_demand"]},
            "skill": {"skills": [], "note": "Skill-Loop Phase 2"},
            "enterprise": get_enterprise_profile(tenant_id).model_dump(mode="json"),
        }

    return asyncio.run(resolve_context_async(intent, tenant_id, params))
