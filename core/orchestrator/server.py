"""AI-OS v2 — thin Orchestrator (Phase-1 skeleton)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

from .audit import write_agent_run
from .context_resolution import resolve_context
from .dataproducts import DP_CLASS_BY_NODE_TYPE
from .dispatch import dispatch
from .dp_service import DPCommitError, commit_dataproduct, kg_stats, resolve_node_by_id
from .intent_router import route_intent
from .kg_search import list_nodes, search_nodes

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestrator"}


@app.post("/v1/dispatch", response_model=DispatchResponse)
async def dispatch_intent(req: DispatchRequest) -> DispatchResponse:
    intent = route_intent(req.intent, req.params)
    context_bundle = resolve_context(intent, req.tenant_id, req.params)
    result = await dispatch(intent, context_bundle, req.tenant_id, req.params)
    write_agent_run(intent, result, req.tenant_id)
    return DispatchResponse(
        status="ok",
        intent=intent,
        result=result,
        context_bundle=context_bundle,
    )


@app.get("/v1/brain/offerings")
async def list_offerings() -> dict[str, Any]:
    from .brain_store import list_offerings as _list

    return {"offerings": _list()}


@app.get("/v1/brain/engagements")
async def list_engagements(status: str | None = None) -> dict[str, Any]:
    from .brain_store import list_engagements as _list

    return {"engagements": _list(status=status)}


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
