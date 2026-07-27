"""daily_open_loops — Engagements + Meetings + Memory + Mail-Stub."""

from __future__ import annotations

from typing import Any

from ..brain_store import active_engagements, meetings_today, offering_by_id
from ..mcp_clients import calendar_stub, mail_stub
from . import memory_ask


async def run(
    context_bundle: dict[str, Any],
    tenant_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    engagements = active_engagements()
    meetings = meetings_today()
    mail = await mail_stub.list_open_actions(tenant_id)
    cal = await calendar_stub.list_today(tenant_id)
    if cal.get("meetings"):
        meetings = cal["meetings"]

    meeting_bullets: list[str] = []
    try:
        from ..meetings_store import list_meetings
        open_meeting_items = list_meetings(tenant_id, has_open_todo=True, limit=20)
        for m in open_meeting_items:
            for todo in m.get("todos", []):
                if isinstance(todo, dict) and not todo.get("done"):
                    todo_text = todo.get("text") or todo.get("task") or "To-Do klären"
                    meeting_bullets.append(f"{m['title']}: {todo_text}")
    except Exception:
        pass

    engagement_bullets: list[str] = []
    for e in engagements:
        off = offering_by_id(str(e.get("offering_id", "")))
        off_name = off["name"] if off else e.get("offering_id", "?")
        next_step = e.get("next_step") or "nächsten Schritt klären"
        engagement_bullets.append(
            f"{e['title']} ({e.get('status')}, Offering: {off_name}) — {next_step}"
        )

    calendar_bullets: list[str] = []
    for m in meetings[:5]:
        calendar_bullets.append(
            f"Termin: {m.get('title')} · {m.get('when', 'heute')} — {m.get('note', '')}".strip(" —")
        )

    sections: list[str] = []
    if meeting_bullets:
        sections.append(
            "**Offene Aufgaben aus Meetings** ([Meetings öffnen](/meetings)):\n"
            + "\n".join(f"• {b}" for b in meeting_bullets)
        )

    if engagement_bullets:
        sections.append(
            "**Aktive Projekte & Engagements** ([Projekte öffnen](/portfolio)):\n"
            + "\n".join(f"• {b}" for b in engagement_bullets)
        )

    # Only show calendar section if a real (non-stub/seed) calendar adapter is connected
    if cal.get("status") in {"connected", "live"} and calendar_bullets:
        sections.append(
            "**Heutige Termine:**\n"
            + "\n".join(f"• {b}" for b in calendar_bullets)
        )

    # Only show email section if a real (non-stub) mail adapter is connected
    if mail.get("status") in {"connected", "live"} and mail.get("actions"):
        mail_bullets = [f"Mail: {a.get('subject')} — {a.get('action')}" for a in mail["actions"][:5]]
        if mail_bullets:
            sections.append("**E-Mail Aktionen:**\n" + "\n".join(f"• {b}" for b in mail_bullets))

    # Kurz-Memory als Hintergrund — nutzt aktiven Compute-Modus oder sovereign
    active_compute = params.get("compute_mode") or "sovereign"
    mem = await memory_ask.run(
        context_bundle,
        tenant_id,
        {
            **params,
            "query": "Was war heute werkstattseitig relevant? Nur Stichworte.",
            "compute_mode": active_compute,
        },
    )
    mem_note = str(mem.get("answer") or "").strip()
    if mem_note and mem_note not in {"Keine Antwort.", "—"} and "nicht erreichbar" not in mem_note:
        sections.append(f"**Gedächtnis & Notizen:**\n{mem_note}")

    nav_footer = "\n\n📌 **Direkt-Absprung:**\n👉 [Meetings-Übersicht öffnen](/meetings)\n👉 [Projekt-Portfolio öffnen](/portfolio)"
    header = "Tagesübersicht — Offene Punkte, Termine & Projekte:"

    if not sections:
        answer = f"{header}\n\nKeine aktuellen offenen Punkte oder Engagements vorhanden.{nav_footer}"
    else:
        answer = f"{header}\n\n" + "\n\n".join(sections) + nav_footer
    model = mem.get("model") or "orchestrator+rules"

    sources = [
        {
            "id": e["id"],
            "role": "engagement",
            "title": e["title"],
            "snippet": e.get("next_step", ""),
            "chat_id": "",
            "source": "brain-seed",
            "ingested_at": "",
        }
        for e in engagements
    ]
    sources.extend(mem.get("sources") or [])

    return {
        "kind": "ask",
        "answer": answer,
        "mode": "daily_open_loops",
        "detail": False,
        "model": model,
        "sources": sources[:12],
        "sourceCount": len(sources),
        "mail_stub": mail.get("status"),
        "calendar_stub": cal.get("status"),
        "tenant_id": tenant_id,
    }
