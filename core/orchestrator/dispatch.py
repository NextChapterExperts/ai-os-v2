"""Dispatch handlers for skeleton intents."""

from __future__ import annotations

from typing import Any

from .handlers import daily_open_loops, invoice_pipeline, mail_triage, memory_ask, unified_search


async def dispatch(
    intent: str,
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    if intent == "ping":
        return {
            "answer": "pong",
            "kind": "ping",
            "sources": [],
            "sourceCount": 0,
        }

    if intent == "handwerk_angebot":
        import core.workflow_engine.sample_workflows  # noqa: F401
        import core.workflow_engine.meetings_workflows  # noqa: F401
        from core.workflow_engine.generic_runner import execute_registered_workflow
        res = await execute_registered_workflow("handwerk-angebot", tenant_id, {
            "kunden_name": params.get("kunden_name") or "Malerbetrieb Schulze",
            "projekt_titel": params.get("projekt_titel") or "Fassadenanstrich",
            "umfang_qm": float(params.get("umfang_qm") or 100.0),
            "stundensatz": float(params.get("stundensatz") or 70.0),
        })
        return {
            "answer": res["result"]["angebot_text"],
            "kind": "workflow",
            "workflow_result": res,
            "sources": [],
            "sourceCount": 0,
        }

    if intent == "daily_open_loops":
        return await daily_open_loops.run(context_bundle, tenant_id, params)

    if intent == "memory_ask":
        return await memory_ask.run(context_bundle, tenant_id, params)

    if intent == "mail_triage":
        return await mail_triage.run(context_bundle, tenant_id, params)

    if intent in ("invoice_run", "invoice_pipeline", "rechnungen"):
        return await invoice_pipeline.run_invoice_pipeline(context_bundle, tenant_id, params)

    if intent in ("invoice_export", "steuer_export", "export_steuer"):
        return await invoice_pipeline.run_invoice_export(context_bundle, tenant_id, params)

    if intent == "unified_search":
        return await unified_search.run(context_bundle, tenant_id, params)

    return {
        "answer": f"Unbekannter Intent «{intent}» — Fallback memory_ask.",
        "kind": "unknown",
        "fallback": await memory_ask.run(context_bundle, tenant_id, params),
        "sources": [],
        "sourceCount": 0,
    }
