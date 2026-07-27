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

    bullets: list[str] = []
    for e in engagements:
        off = offering_by_id(str(e.get("offering_id", "")))
        off_name = off["name"] if off else e.get("offering_id", "?")
        next_step = e.get("next_step") or "nächsten Schritt klären"
        bullets.append(
            f"**{e['title']}** ({e.get('status')}, Offering: {off_name}) — {next_step}"
        )

    for m in meetings[:5]:
        bullets.append(
            f"Termin: **{m.get('title')}** · {m.get('when', 'heute')} — {m.get('note', '')}".strip(
                " —"
            )
        )

    for a in mail.get("actions", [])[:5]:
        bullets.append(f"Mail: **{a.get('subject')}** — {a.get('action')}")

    try:
        from ..meetings_store import list_meetings
        open_meeting_items = list_meetings(tenant_id, has_open_todo=True, limit=5)
        for m in open_meeting_items:
            for todo in m.get("todos", []):
                if isinstance(todo, dict) and not todo.get("done"):
                    todo_text = todo.get("text") or todo.get("task") or "To-Do klären"
                    bullets.append(f"Meeting To-Do (**{m['title']}**): {todo_text}")
    except Exception:
        pass

    # Kurz-Memory nur als Hintergrund — immer lokal (sovereign), unabhängig vom UI-Modus
    mem = await memory_ask.run(
        context_bundle,
        tenant_id,
        {
            **params,
            "query": "Was war heute werkstattseitig relevant? Nur Stichworte.",
            "compute_mode": "sovereign",
        },
    )

    if not bullets:
        answer = (
            "Keine offenen Engagements oder Termine im Seed.\n\n"
            f"Werkstatt-Gedächtnis: {mem.get('answer', '—')}"
        )
        model = mem.get("model") or "orchestrator+rules"
    else:
        body = "\n".join(f"• {b}" for b in bullets[:8])
        mail_note = mail.get("status_note", "")
        mem_note = str(mem.get("answer") or "").strip()
        if mem_note and mem_note not in {"Keine Antwort.", "—"}:
            mem_note = f"\n\nGedächtnis: {mem_note}"
        else:
            mem_note = ""
        answer = (
            f"Offene Schleifen heute:\n{body}\n\n"
            f"{mail_note}{mem_note}\n"
            "Details oder Mail-Triage: einfach nachfragen."
        ).strip()
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
