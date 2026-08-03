"""MCP calendar-Adapter — Google Calendar über core/google."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from core.google import auth as google_auth
from core.google import calendar_client
from core.mcp_gateway.adapters.registry import register


@register("calendar", "get_today")
def calendar_get_today(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("dry_run"):
        return {
            "ok": True,
            "dry_run": True,
            "date": date.today().isoformat(),
            "summary": "[Dry-Run] Keine Termine.",
            "events": [],
            "status": "dry-run",
        }
    if not google_auth.secrets_configured():
        return {
            "ok": True,
            "date": date.today().isoformat(),
            "summary": "Kalender-MCP Stub — token.json unter secrets/google/ fehlt.",
            "events": [],
            "status": "stub",
        }

    today = date.today()
    events = calendar_client.fetch_events_for_day(today, interactive=False)
    summary = calendar_client.format_day_summary(events, today)
    return {
        "ok": True,
        "date": today.isoformat(),
        "summary": summary,
        "events": events,
        "status": "connected",
    }


@register("calendar", "list_today")
def calendar_list_today(args: dict[str, Any]) -> dict[str, Any]:
    return calendar_get_today(args)


@register("calendar", "get_week")
def calendar_get_week(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("dry_run"):
        return {"ok": True, "dry_run": True, "events": [], "status": "dry-run"}
    start = date.today()
    end = start + timedelta(days=6)
    events = calendar_client.fetch_events_for_range(start, end, interactive=False)
    return {
        "ok": True,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "events": events,
        "count": len(events),
        "status": "connected",
    }


@register("calendar", "list_attendees")
def calendar_list_attendees(args: dict[str, Any]) -> dict[str, Any]:
    event_id = args.get("event_id") or args.get("id")
    if not event_id:
        return {"ok": False, "error": "missing_event_id", "message": "event_id erforderlich"}
    ev = calendar_client.get_event(str(event_id), interactive=False)
    return {
        "ok": True,
        "event_id": ev["id"],
        "title": ev["title"],
        "attendees": ev.get("attendees") or [],
    }


@register("calendar", "get_event")
def calendar_get_event(args: dict[str, Any]) -> dict[str, Any]:
    event_id = args.get("event_id") or args.get("id")
    if not event_id:
        return {"ok": False, "error": "missing_event_id", "message": "event_id erforderlich"}
    ev = calendar_client.get_event(str(event_id), interactive=False)
    return {"ok": True, "event": ev}


@register("calendar", "list_events")
def calendar_list_events(args: dict[str, Any]) -> dict[str, Any]:
    result = calendar_get_today(args)
    events = result.get("events") or []
    return {
        "ok": result.get("ok", True),
        "date": result.get("date") or date.today().isoformat(),
        "events": events,
        "count": len(events),
        "status": result.get("status"),
    }
