"""Deterministic intent routing (P4) — no LLM."""

from __future__ import annotations

from typing import Any


def route_intent(raw: str, params: dict[str, Any] | None = None) -> str:
    params = params or {}
    if params.get("force_intent"):
        return str(params["force_intent"])

    text = (raw or "").strip()
    lower = text.lower()

    if text in {"ping", "health"}:
        return "ping"

    if any(
        k in lower
        for k in (
            "heute noch",
            "muss ich",
            "open loop",
            "offen",
            "todo",
            "aufgaben",
            "was steht an",
            "heute machen",
            "noch machen",
        )
    ):
        return "daily_open_loops"

    if any(
        k in lower
        for k in (
            "haben wir schon mal",
            "schon mal daran gearbeitet",
            "durchsuche",
            "suche nach",
            "finde dateien",
            "in welchem projekt",
        )
    ):
        return "unified_search"

    if any(
        k in lower
        for k in (
            "was haben wir",
            "zusammenfass",
            "gedächtnis",
            "heute gemacht",
            "bisher",
            "stand der dinge",
            "stand im",
            "stand des",
            "projektstand",
            "fortschritt",
            "1100-ai-os",
            "ai-os-v2",
        )
    ):
        return "memory_ask"

    # Default: treat free text as memory/orchestrator question
    if "?" in text or len(text.split()) >= 3:
        if any(k in lower for k in ("mail", "inbox", "e-mail", "email")):
            return "mail_triage"
        return "memory_ask"

    return "memory_ask"
