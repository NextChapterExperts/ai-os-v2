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

@register("calendar", "list_events_range")
def calendar_list_events_range(args: dict[str, Any]) -> dict[str, Any]:
    start_raw = args.get("start_date") or args.get("since_date") or "2026-07-01"
    end_raw = args.get("end_date") or args.get("until_date")
    dry_run = bool(args.get("dry_run"))
    max_results = int(args.get("max_results") or 250)
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "start_date": str(start_raw)[:10],
            "end_date": str(end_raw or date.today().isoformat())[:10],
            "events": [],
            "count": 0,
        }
    if not google_auth.secrets_configured():
        return {
            "ok": True,
            "status": "stub",
            "events": [],
            "count": 0,
            "message": "token.json fehlt",
        }
    try:
        start_day = date.fromisoformat(str(start_raw)[:10])
        end_day = date.fromisoformat(str(end_raw)[:10]) if end_raw else date.today()
    except ValueError:
        return {"ok": False, "error": "invalid_date", "message": "start_date/end_date ungültig"}
    events = calendar_client.fetch_events_for_range_paginated(
        start_day, end_day, max_results=max_results, interactive=False,
    )
    return {
        "ok": True,
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "events": events,
        "count": len(events),
        "status": "connected",
    }

