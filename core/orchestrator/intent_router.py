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

    # 1. Explicit search commands take precedence over general open-loop keywords
    if any(
        k in lower
        for k in (
            "suche nach",
            "ich suche",
            "durchsuche",
            "finde dateien",
            "haben wir schon mal",
            "schon mal daran gearbeitet",
            "in welchem projekt",
        )
    ):
        return "unified_search"

    # 2. Specific meeting queries take precedence over generic daily open loops
    if any(
        k in lower
        for k in (
            "punkte aus meeting",
            "punkte aus den meeting",
            "punkte aus besprechung",
            "meeting todo",
            "meeting to-do",
            "meeting notizen",
            "beschlüsse",
        )
    ):
        return "unified_search"

    # 3. Standard Prompt Catalog — Daily Focus & Open Loops
    if any(
        k in lower
        for k in (
            "was ist noch offen",
            "was steht noch aus",
            "was liegt an",
            "was müsste gemacht werden",
            "wichtige punkte für heute",
            "heute noch",
            "muss ich",
            "open loop",
            "was steht an",
            "was steht heute",
            "steht heute an",
            "heute an",
            "heute machen",
            "noch machen",
            "offen",
            "todo",
            "aufgaben",
        )
    ):
        return "daily_open_loops"

    # 4. Standard Prompt Catalog — Project Status & Summaries
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
            "wie ist der stand",
            "status von",
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

