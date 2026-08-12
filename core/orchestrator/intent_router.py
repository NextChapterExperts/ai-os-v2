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

    # 0. Workflow triggers
    if any(k in lower for k in ("recherche", "recherchiere", "internet suche", "web-suche", "web suche", "research")):
        return "research"

    if any(k in lower for k in ("angebot ersteller", "angebot erstellen", "handwerk angebot", "handwerker angebot", "erstelle angebot", "erstelle ein angebot")):
        return "handwerk_angebot"

    # 1. Explicit search commands take precedence over open-loop keywords
    if any(
        k in lower
        for k in (
            "ich suche nach",
            "suche nach",
            "durchsuche",
            "finde dateien",
        )
    ):
        return "unified_search"

    # 2. Meeting & Open Loop Summary queries route to daily_open_loops (synthesized summary)
    if any(
        k in lower
        for k in (
            "punkte aus meeting",
            "punkte aus den meeting",
            "punkte aus besprechung",
            "meeting todo",
            "meeting to-do",
            "meeting notizen",
        )
    ):
        return "daily_open_loops"

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

    if any(k in lower for k in ("rechnung", "invoice", "steuer export", "steuer-export")):
        if any(k in lower for k in ("export", "steuer", "pdf")):
            return "invoice_export"
        return "invoice_run"

    # Default: treat free text as memory/orchestrator question
    if "?" in text or len(text.split()) >= 3:
        if any(k in lower for k in ("mail", "inbox", "e-mail", "email")):
            return "mail_triage"
        return "memory_ask"

    return "memory_ask"

