"""AI-OS v2 — thin Orchestrator (Phase-1 skeleton)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .audit import write_agent_run
from .context_resolution import resolve_context
from .dispatch import dispatch
from .intent_router import route_intent

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
