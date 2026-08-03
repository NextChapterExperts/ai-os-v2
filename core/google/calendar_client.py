"""Google Calendar — Termine für Briefing und MCP calendar-Adapter."""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from . import auth


class CalendarConfigError(RuntimeError):
    pass


def _local_tz() -> ZoneInfo:
    name = os.getenv("AI_OS_TIMEZONE", "Europe/Berlin").strip() or "Europe/Berlin"
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("Europe/Berlin")


def _service(*, interactive: bool = False):
    from googleapiclient.discovery import build

    creds = auth.load_for_tool("calendar", "get_today", interactive=interactive)
    return build("calendar", "v3", credentials=creds)


def _event_start_label(event: dict[str, Any], tz: ZoneInfo) -> str:
    start = event.get("start") or {}
    raw = start.get("dateTime") or start.get("date") or ""
    if not raw:
        return ""
    if "T" in raw:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            return dt.astimezone(tz).strftime("%H:%M")
        except ValueError:
            return raw[:16]
    return "ganztägig"


def fetch_events_for_day(
    day: date | None = None,
    *,
    max_results: int = 25,
    interactive: bool = False,
) -> list[dict[str, Any]]:
    """Termine für einen Kalendertag (lokal, Europe/Berlin)."""
    tz = _local_tz()
    target = day or datetime.now(tz).date()
    start_dt = datetime.combine(target, time.min, tzinfo=tz)
    end_dt = start_dt + timedelta(days=1)

    try:
        service = _service(interactive=interactive)
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_dt.isoformat(),
                timeMax=end_dt.isoformat(),
                maxResults=max(1, min(max_results, 50)),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except ImportError as exc:
        raise CalendarConfigError(
            f"Google-Bibliotheken fehlen ({exc}). pip install -r core/google/requirements.txt"
        ) from exc
    except Exception as exc:
        raise CalendarConfigError(f"Kalender-API Fehler: {exc}") from exc

    items = events_result.get("items") or []
    out: list[dict[str, Any]] = []
    for ev in items:
        attendees = []
        for att in ev.get("attendees") or []:
            attendees.append({
                "email": att.get("email") or "",
                "name": att.get("displayName") or "",
                "response": att.get("responseStatus") or "",
            })
        out.append({
            "id": ev.get("id") or "",
            "title": ev.get("summary") or "(Kein Titel)",
            "start": _event_start_label(ev, tz),
            "location": ev.get("location") or "",
            "status": ev.get("status") or "",
            "attendees": attendees,
        })
    return out


def fetch_events_for_range(
    start_day: date,
    end_day: date,
    *,
    max_results: int = 50,
    interactive: bool = False,
) -> list[dict[str, Any]]:
    """Termine für einen Datumsbereich (inklusive start_day, exklusive end_day+1)."""
    tz = _local_tz()
    start_dt = datetime.combine(start_day, time.min, tzinfo=tz)
    end_dt = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=tz)

    service = _service(interactive=interactive)
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            maxResults=max(1, min(max_results, 100)),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    items = events_result.get("items") or []
    out: list[dict[str, Any]] = []
    for ev in items:
        out.append({
            "id": ev.get("id") or "",
            "title": ev.get("summary") or "(Kein Titel)",
            "start": _event_start_label(ev, tz),
            "location": ev.get("location") or "",
            "status": ev.get("status") or "",
        })
    return out


def get_event(event_id: str, *, interactive: bool = False) -> dict[str, Any]:
    service = _service(interactive=interactive)
    ev = service.events().get(calendarId="primary", eventId=event_id).execute()
    attendees = []
    for att in ev.get("attendees") or []:
        attendees.append({
            "email": att.get("email") or "",
            "name": att.get("displayName") or "",
            "response": att.get("responseStatus") or "",
        })
    return {
        "id": ev.get("id") or "",
        "title": ev.get("summary") or "",
        "description": ev.get("description") or "",
        "location": ev.get("location") or "",
        "attendees": attendees,
        "start": ev.get("start") or {},
        "end": ev.get("end") or {},
    }


def format_day_summary(events: list[dict[str, Any]], day: date) -> str:
    if not events:
        return f"Keine Termine am {day.strftime('%d.%m.%Y')}."
    lines = [f"{len(events)} Termin(e) am {day.strftime('%d.%m.%Y')}:"]
    for ev in events:
        loc = f" ({ev['location']})" if ev.get("location") else ""
        lines.append(f"- {ev.get('start', '??:??')} {ev.get('title', '')}{loc}")
    return "\n".join(lines)
