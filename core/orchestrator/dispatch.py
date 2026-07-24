"""Dispatch handlers for skeleton intents."""

from __future__ import annotations

from typing import Any

from .handlers import daily_open_loops, mail_triage, memory_ask


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

    if intent == "daily_open_loops":
        return await daily_open_loops.run(context_bundle, tenant_id, params)

    if intent == "memory_ask":
        return await memory_ask.run(context_bundle, tenant_id, params)

    if intent == "mail_triage":
        return await mail_triage.run(context_bundle, tenant_id, params)

    return {
        "answer": f"Unbekannter Intent «{intent}» — Fallback memory_ask.",
        "kind": "unknown",
        "fallback": await memory_ask.run(context_bundle, tenant_id, params),
        "sources": [],
        "sourceCount": 0,
    }
