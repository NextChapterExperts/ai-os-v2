"""AI-OS v2 — thin Orchestrator (Phase-1 skeleton)."""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

from .audit import write_agent_run
from .context_resolution import resolve_context
from .dataproducts import DP_CLASS_BY_NODE_TYPE
from .dispatch import dispatch
from .dp_service import DPCommitError, commit_dataproduct, kg_stats, resolve_node_by_id
from .intent_router import route_intent
from .kg_search import list_nodes, search_nodes
from .run_context_store import load_run_context, save_run_context

from core.memory_gateway.client import chat_completion, list_models

app = FastAPI(title="AI-OS Orchestrator", version="2.0.0-skeleton")


class DispatchRequest(BaseModel):
    intent: str
    tenant_id: str = "nextchapter"
    params: dict[str, Any] = Field(default_factory=dict)


class DispatchResponse(BaseModel):
    status: str
    intent: str
    result: dict[str, Any]
    context_bundle: dict[str, Any]
    run_id: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestrator"}


@app.post("/v1/dispatch", response_model=DispatchResponse)
async def dispatch_intent(req: DispatchRequest) -> DispatchResponse:
    from core.memory.run_distill import distill_after_run
    from core.memory.tactical_memory import ensure_workflow, record_from_params
    from core.memory.working_memory import append_from_dispatch, ensure_run

    run_id = str(req.params.get("run_id") or req.params.get("session_id") or uuid.uuid4())
    workflow_run_id = req.params.get("workflow_run_id")
    params = {**req.params, "run_id": run_id}

    intent = route_intent(req.intent, params)
    ensure_run(run_id, req.tenant_id, intent=intent)
    if workflow_run_id:
        ensure_workflow(str(workflow_run_id), req.tenant_id, name=intent)

    context_bundle = resolve_context(intent, req.tenant_id, params)
    result = await dispatch(intent, context_bundle, req.tenant_id, params)
    append_from_dispatch(run_id, intent, result)
    if workflow_run_id:
        record_from_params(str(workflow_run_id), params, result)

    distill = distill_after_run(
        req.tenant_id,
        run_id,
        str(workflow_run_id) if workflow_run_id else None,
        intent,
        result,
    )
    llm_context = result.pop("llmContext", None)
    if llm_context:
        llm_context["orchestratorContext"] = context_bundle
        save_run_context(run_id, llm_context)
        result["hasContext"] = True
    result["runId"] = run_id
    write_agent_run(intent, result, req.tenant_id, extra={"run_id": run_id, "distill": distill})
    return DispatchResponse(
        status="ok",
        intent=intent,
        result=result,
        context_bundle=context_bundle,
        run_id=run_id,
    )


@app.get("/v1/runs/{run_id}/context")
async def get_run_context(run_id: str) -> dict[str, Any]:
    context = load_run_context(run_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Run context not found")
    return context


@app.get("/v1/brain/offerings")
async def list_offerings() -> dict[str, Any]:
    from .brain_store import list_offerings as _list

    return {"offerings": _list()}


@app.get("/v1/brain/engagements")
async def list_engagements(status: str | None = None) -> dict[str, Any]:
    from .brain_store import list_engagements as _list

    return {"engagements": _list(status=status)}


class MeetingTodo(BaseModel):
    text: str
    done: bool = False


class MeetingWriteRequest(BaseModel):
    title: str
    held_at: str
    participants: str = ""
    summary: str = ""
    engagement_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    todos: list[MeetingTodo] = Field(default_factory=list)


class MeetingPatchRequest(BaseModel):
    title: str | None = None
    held_at: str | None = None
    participants: str | None = None
    summary: str | None = None
    engagement_ids: list[str] | None = None
    tags: list[str] | None = None
    todos: list[MeetingTodo] | None = None


@app.get("/v1/meetings")
async def meetings_list(
    tenant_id: str = "nextchapter",
    q: str | None = None,
    unassigned: bool = False,
    has_open_todo: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    from .meetings_store import list_engagement_options, list_meetings

    items = list_meetings(
        tenant_id,
        q=q,
        unassigned=unassigned,
        has_open_todo=has_open_todo,
        limit=limit,
    )
    return {
        "tenant_id": tenant_id,
        "meetings": items,
        "count": len(items),
        "engagement_options": list_engagement_options(),
    }


@app.get("/v1/meetings/{meeting_id}")
async def meetings_get(meeting_id: str, tenant_id: str = "nextchapter") -> dict[str, Any]:
    from .meetings_store import get_meeting, list_engagement_options

    item = get_meeting(meeting_id, tenant_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting": item, "engagement_options": list_engagement_options()}


@app.post("/v1/meetings")
async def meetings_create(req: MeetingWriteRequest, tenant_id: str = "nextchapter") -> dict[str, Any]:
    from .meetings_store import create_meeting

    try:
        item = create_meeting(
            tenant_id,
            {
                **req.model_dump(),
                "todos": [t.model_dump() for t in req.todos],
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"meeting": item}


@app.patch("/v1/meetings/{meeting_id}")
async def meetings_update(
    meeting_id: str,
    req: MeetingPatchRequest,
    tenant_id: str = "nextchapter",
) -> dict[str, Any]:
    from .meetings_store import update_meeting

    payload = req.model_dump(exclude_unset=True)
    if "todos" in payload and payload["todos"] is not None:
        payload["todos"] = [t if isinstance(t, dict) else t.model_dump() for t in payload["todos"]]
    try:
        item = update_meeting(meeting_id, tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting": item}


@app.delete("/v1/meetings/{meeting_id}")
async def meetings_delete(meeting_id: str, tenant_id: str = "nextchapter") -> dict[str, Any]:
    from .meetings_store import delete_meeting

    if not delete_meeting(meeting_id, tenant_id):
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "deleted", "id": meeting_id}


class DataProductCommitRequest(BaseModel):
    node_type: str
    tenant_id: str = "nextchapter"
    produced_by: str
    workflow_run_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


@app.post("/v1/dataproduct/commit")
async def commit_dataproduct_endpoint(req: DataProductCommitRequest) -> dict[str, Any]:
    dp_cls = DP_CLASS_BY_NODE_TYPE.get(req.node_type)
    if dp_cls is None:
        raise HTTPException(status_code=400, detail=f"Unbekannter node_type: {req.node_type}")
    try:
        dp = dp_cls(
            tenant_id=req.tenant_id,
            produced_by=req.produced_by,
            workflow_run_id=req.workflow_run_id,
            **req.payload,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    try:
        return commit_dataproduct(dp, dry_run=req.dry_run)
    except DPCommitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/dataproduct/resolve/{node_id}")
async def resolve_dataproduct(node_id: str, tenant_id: str = "nextchapter") -> dict[str, Any]:
    node = resolve_node_by_id(tenant_id, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node nicht gefunden")
    return node


@app.get("/v1/kg/stats")
async def get_kg_stats(tenant_id: str = "nextchapter") -> dict[str, Any]:
    return kg_stats(tenant_id)


@app.get("/v1/kg/search")
async def get_kg_search(
    q: str, tenant_id: str = "nextchapter", node_type: str | None = None, limit: int = 10
) -> dict[str, Any]:
    node_types = [node_type] if node_type else None
    results = search_nodes(tenant_id, q, node_types=node_types, limit=limit)
    return {"query": q, "tenant_id": tenant_id, "results": results, "count": len(results)}


@app.get("/v1/kg/nodes")
async def get_kg_nodes(
    node_type: str, tenant_id: str = "nextchapter", limit: int = 200
) -> dict[str, Any]:
    results = list_nodes(tenant_id, node_type, limit=limit)
    return {"node_type": node_type, "tenant_id": tenant_id, "results": results, "count": len(results)}


class ChatImportRequest(BaseModel):
    transcript: dict[str, Any]
    tenant_id: str = "nextchapter"
    project_id: str | None = None


@app.post("/v1/chat-import")
async def post_chat_import(req: ChatImportRequest) -> dict[str, Any]:
    """Phase 1b — externe Chats (Antigravity, Gemini, …) ins Gedächtnis."""
    from .chat_import import import_transcript

    try:
        return import_transcript(
            req.transcript,
            tenant_id=req.tenant_id,
            project_id=req.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/v1/capture/stats")
async def get_capture_stats() -> dict[str, Any]:
    """Status der Chat-Capture-Dienste (Cursor, Antigravity, Inbox)."""
    import json
    import sqlite3
    from pathlib import Path

    memory_root = Path(os.environ.get("AIOS_MEMORY_ROOT", "/opt/ai-os/memory"))
    db_path = os.environ.get("AIOS_MEMORY_DB", str(memory_root / "memory.db"))
    stats: dict[str, Any] = {"sources": {}, "inbox_path": "/opt/ai-os/ingest/inbox"}

    if os.path.exists(db_path):
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute(
                "SELECT source, COUNT(*) AS n FROM chunks GROUP BY source ORDER BY n DESC"
            ).fetchall()
            stats["sources"] = {r["source"]: r["n"] for r in rows}
            stats["total_chunks"] = sum(stats["sources"].values())
            meta = con.execute("SELECT key, value FROM capture_meta").fetchall()
            stats["capture_meta"] = {r["key"]: r["value"] for r in meta}
        finally:
            con.close()

    for name, rel in [
        ("antigravity", "state/antigravity-poller-state.json"),
        ("gemini_inbox", "state/gemini-inbox-state.json"),
    ]:
        p = memory_root / rel
        if p.is_file():
            try:
                stats[name] = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                stats[name] = {"error": "invalid json"}

    return stats


class ChatCompletionRequest(BaseModel):
    messages: list[dict[str, Any]]
    tenant_id: str = "nextchapter"
    model: str | None = None
    compute_mode: str | None = None
    produced_by: str = "memory-gateway"
    session_id: str | None = None
    project_id: str | None = None
    temperature: float = 0.2
    max_tokens: int = 512
    persist: bool = True


@app.get("/v1/models")
async def get_models() -> dict[str, Any]:
    """Memory Gateway — Modellliste + Compute-Modi (Phase 1, P11/P19)."""
    return await list_models()


@app.post("/v1/chat/completions")
async def post_chat_completions(req: ChatCompletionRequest) -> dict[str, Any]:
    """Memory Gateway — Inference + Persist-Hook (nie optional in PROD)."""
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages required")
    try:
        return await chat_completion(
            req.messages,
            tenant_id=req.tenant_id,
            model=req.model,
            compute_mode=req.compute_mode,
            produced_by=req.produced_by,
            session_id=req.session_id,
            project_id=req.project_id,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            persist=req.persist,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text[:500],
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


class SearchRequest(BaseModel):
    query: str
    tenant_id: str = "nextchapter"
    limit: int = 8


@app.post("/v1/search")
async def post_search(req: SearchRequest) -> dict[str, Any]:
    """Dedizierter Unified-Search-Endpoint (Phase 1, ROADMAP §6.5)."""
    from .handlers import unified_search

    return await unified_search.run({}, req.tenant_id, {"query": req.query, "limit": req.limit})


class MemorySyncRequest(BaseModel):
    tenant_id: str = "nextchapter"
    since: str | None = None
    source: str | None = None
    limit: int | None = None
    dry_run: bool = False
    force: bool = False


@app.post("/v1/memory/sync-letta")
async def post_memory_sync_letta(req: MemorySyncRequest) -> dict[str, Any]:
    """SQLite chunks → Letta L2 (Backfill / Live-Sync)."""
    from core.memory_gateway.letta_sync import sync_sqlite_to_letta

    return sync_sqlite_to_letta(
        req.tenant_id,
        since=req.since,
        source=req.source,
        limit=req.limit,
        dry_run=req.dry_run,
        force=req.force,
    )


@app.post("/v1/memory/rebuild-fts")
async def post_memory_rebuild_fts() -> dict[str, Any]:
    """FTS5-Index aus chunks neu aufbauen."""
    from core.memory_gateway.sqlite_schema import rebuild_fts

    return rebuild_fts()


class L3CurateRequest(BaseModel):
    tenant_id: str = "nextchapter"
    dry_run: bool = False
    force: bool = False


class L2CurateRequest(BaseModel):
    tenant_id: str = "nextchapter"
    day_offset: int | None = None
    dry_run: bool = False
    force: bool = False


@app.post("/v1/memory/curate/l2")
async def post_l2_curate(req: L2CurateRequest) -> dict[str, Any]:
    """L2-Curator — L1-Chunks (24h) zu Tagesdigest in Letta Archival."""
    from core.memory.l2_curator import run_l2_curate

    return await run_l2_curate(
        req.tenant_id,
        day_offset=req.day_offset,
        dry_run=req.dry_run,
        force=req.force,
    )


@app.post("/v1/memory/curate/l3")
async def post_l3_curate(req: L3CurateRequest) -> dict[str, Any]:
    """L3-Curator — Fakten aus L2 Archival → org:Claim + Letta Core."""
    from core.memory.l3_curator import run_l3_curate

    return await run_l3_curate(req.tenant_id, dry_run=req.dry_run, force=req.force)


@app.get("/v1/memory/curate/l3/pending")
async def get_l3_pending_claims() -> dict[str, Any]:
    """Claims mit supports_refs — warten auf Human-Gate."""
    from core.memory.l3_curator import get_pending_claims

    claims = get_pending_claims()
    return {"count": len(claims), "claims": claims}


class L1CurateRequest(BaseModel):
    dry_run: bool = False
    modes: list[str] = Field(default_factory=lambda: ["stats", "exact_dedup", "semantic_dedup", "rolling"])


@app.get("/v1/memory/l1/stats")
async def get_l1_stats() -> dict[str, Any]:
    """L1 Qdrant `content` — Statistik."""
    from core.memory.l1_curator import scan_stats

    return scan_stats()


@app.get("/v1/memory/storage")
async def get_memory_storage() -> dict[str, Any]:
    """Speicherverbrauch aller Memory-Stacks + VM-Festplatte."""
    from core.memory.storage_stats import collect_storage_stats

    return collect_storage_stats()


@app.post("/v1/memory/curate/l1")
async def post_l1_curate(req: L1CurateRequest) -> dict[str, Any]:
    """L1-Curator — Qdrant Dedup + Rolling Retention."""
    from core.memory.l1_curator import run_l1_curate

    return run_l1_curate(modes=req.modes, dry_run=req.dry_run)


@app.get("/v1/memory/working/{run_id}")
async def get_working_memory(run_id: str) -> dict[str, Any]:
    from core.memory.working_memory import get_snapshot

    snap = get_snapshot(run_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Working-Memory nicht gefunden")
    return snap


@app.get("/v1/memory/tactical/{workflow_run_id}")
async def get_tactical_memory(workflow_run_id: str) -> dict[str, Any]:
    from core.memory.tactical_memory import get_snapshot

    snap = get_snapshot(workflow_run_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Tactical-Memory nicht gefunden")
    return snap


class WorkingNoteRequest(BaseModel):
    text: str
    kind: str = "scratch"


@app.post("/v1/memory/working/{run_id}/note")
async def post_working_note(run_id: str, req: WorkingNoteRequest) -> dict[str, Any]:
    from core.memory.working_memory import append_note, ensure_run

    ensure_run(run_id, "nextchapter")
    data = append_note(run_id, req.text, kind=req.kind)
    if data is None:
        raise HTTPException(status_code=404, detail="Working-Memory nicht gefunden")
    return data
