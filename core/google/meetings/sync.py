"""Kalender → Meeting-Inbox Sync (deterministisch, kein LLM)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from core.google import auth as google_auth
from core.google import calendar_client
from core.google.meetings.project_parse import (
    build_project_catalog,
    list_discovered_projects,
    match_engagement_ids,
    resolve_project_from_title,
)
from core.orchestrator.brain_store import list_engagements, list_offerings
from core.orchestrator.meetings_store import (
    _format_participants,
    compute_person_meeting_stats,
    upsert_calendar_meeting,
)

DEFAULT_SINCE = "2026-07-01"


def _local_today() -> date:
    tz = calendar_client._local_tz()
    return datetime.now(tz).date()


def _parse_since(since: str | None) -> date:
    raw = (since or DEFAULT_SINCE).strip()[:10]
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date.fromisoformat(DEFAULT_SINCE)


def _skip_event(ev: dict[str, Any]) -> bool:
    if (ev.get("status") or "").lower() == "cancelled":
        return True
    title = str(ev.get("title") or "").strip().lower()
    skip_titles = ("focus time", "block", "abwesenheit", "out of office", "ooo")
    return any(s in title for s in skip_titles)


def _enrich_event(ev: dict[str, Any], catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    raw_title = str(ev.get("title") or "")
    project, display_title = resolve_project_from_title(
        raw_title,
        catalog,
        engagements=list_engagements(),
        offerings=list_offerings(),
    )
    attendees = list(ev.get("attendees") or [])
    engagement_ids = match_engagement_ids(project, list_engagements()) if project else []
    return {
        "raw_title": raw_title,
        "title": display_title or raw_title,
        "project": project,
        "engagement_ids": engagement_ids,
        "attendees": attendees,
        "participants_label": _format_participants(attendees),
    }


def sync_calendar_to_inbox(
    *,
    tenant_id: str = "nextchapter",
    since_date: str | None = None,
    until_date: str | None = None,
    include_forecast: bool = True,
    forecast_days: int = 31,
    dry_run: bool = False,
    max_events: int = 500,
) -> dict[str, Any]:
    since = _parse_since(since_date)
    today = _local_today()
    until = today
    if until_date:
        try:
            until = date.fromisoformat(until_date.strip()[:10])
        except ValueError:
            until = today

    if not google_auth.secrets_configured():
        return {
            "ok": True,
            "status": "stub",
            "dry_run": dry_run,
            "since_date": since.isoformat(),
            "until_date": until.isoformat(),
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "meetings": [],
            "person_stats": [],
            "forecast_next_month": [],
            "summary": "Kalender-Stub — secrets/google/token.json fehlt.",
        }

    try:
        events = calendar_client.fetch_events_for_range_paginated(
            since, until, max_results=max_events, interactive=False,
        )
    except calendar_client.CalendarConfigError as exc:
        return {
            "ok": False,
            "error": "calendar_failed",
            "message": str(exc),
            "since_date": since.isoformat(),
            "until_date": until.isoformat(),
        }

    imported = updated = skipped = 0
    meeting_rows: list[dict[str, Any]] = []

    all_titles = [str(ev.get("title") or "") for ev in events if not _skip_event(ev)]
    catalog = build_project_catalog(
        all_titles,
        engagements=list_engagements(),
        offerings=list_offerings(),
    )

    for ev in events:
        if _skip_event(ev):
            skipped += 1
            continue
        meta = _enrich_event(ev, catalog)
        action, row = upsert_calendar_meeting(
            tenant_id,
            calendar_event_id=str(ev.get("id") or ""),
            title=meta["raw_title"],
            held_at=str(ev.get("held_at") or ""),
            end_at=str(ev.get("end_at") or ""),
            location=str(ev.get("location") or ""),
            attendees=meta["attendees"],
            project=meta["project"],
            engagement_ids=meta["engagement_ids"],
            dry_run=dry_run,
        )
        if action == "created":
            imported += 1
        elif action == "updated":
            updated += 1
        else:
            skipped += 1
        if row:
            meeting_rows.append(_meeting_preview(row))

    person_stats = compute_person_meeting_stats(tenant_id, since_date=since.isoformat())

    forecast: list[dict[str, Any]] = []
    if include_forecast:
        forecast_end = today + timedelta(days=max(1, min(forecast_days, 90)))
        try:
            future_events = calendar_client.fetch_events_for_range_paginated(
                today, forecast_end, max_results=100, interactive=False,
            )
            future_titles = [str(ev.get("title") or "") for ev in future_events if not _skip_event(ev)]
            forecast_catalog = build_project_catalog(
                all_titles + future_titles,
                engagements=list_engagements(),
                offerings=list_offerings(),
            )
            for ev in future_events:
                if _skip_event(ev):
                    continue
                held = str(ev.get("held_at") or "")
                if held and held[:10] < today.isoformat():
                    continue
                meta = _enrich_event(ev, forecast_catalog)
                forecast.append({
                    "held_at": held,
                    "title": meta["title"],
                    "project": meta["project"],
                    "location": str(ev.get("location") or ""),
                    "participants_label": meta["participants_label"],
                    "attendee_emails": [
                        str(a.get("email") or "")
                        for a in meta["attendees"]
                        if isinstance(a, dict) and a.get("email")
                    ],
                    "calendar_event_id": str(ev.get("id") or ""),
                })
        except calendar_client.CalendarConfigError:
            pass

    mode = "Dry-Run" if dry_run else "Live"
    summary = (
        f"Kalender-Sync ({mode}): {imported} neu, {updated} aktualisiert, {skipped} übersprungen "
        f"({since.strftime('%d.%m.%Y')} – {until.strftime('%d.%m.%Y')}). "
        f"{len(person_stats)} Kontakte · Forecast: {len(forecast)} Termine."
    )

    sorted_meetings = sorted(meeting_rows, key=lambda r: r.get("held_at") or "")
    sorted_forecast = sorted(forecast, key=lambda r: r.get("held_at") or "")

    discovered = list_discovered_projects(
        all_titles + [str(f.get("title") or "") for f in forecast],
        engagements=list_engagements(),
        offerings=list_offerings(),
    )

    return {
        "ok": True,
        "status": "connected",
        "dry_run": dry_run,
        "since_date": since.isoformat(),
        "until_date": until.isoformat(),
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "meetings": sorted_meetings[:200],
        "person_stats": person_stats[:100],
        "forecast_next_month": sorted_forecast[:100],
        "discovered_projects": discovered,
        "summary": summary,
    }


def _meeting_preview(row: dict[str, Any]) -> dict[str, Any]:
    refs = row.get("participant_refs") or []
    attendees = [
        {"email": r.get("email", ""), "name": r.get("name", "")}
        for r in refs if isinstance(r, dict)
    ]
    summary = str(row.get("summary") or "").strip()
    tags = row.get("tags") or []
    project = ""
    for tag in tags:
        if isinstance(tag, str) and tag.startswith("project:"):
            project = tag[8:]
            break
    raw_title = str(row.get("title") or "")
    if not project:
        project, _ = resolve_project_from_title(
            raw_title,
            engagements=list_engagements(),
            offerings=list_offerings(),
        )
    _, display_title = resolve_project_from_title(raw_title)
    return {
        "meeting_id": row.get("id", ""),
        "calendar_event_id": row.get("calendar_event_id", ""),
        "project": project,
        "title": display_title or raw_title,
        "held_at": row.get("held_at", ""),
        "end_at": row.get("end_at", ""),
        "location": row.get("location", ""),
        "attendees": attendees,
        "participants_label": str(row.get("participants") or ""),
        "has_summary": bool(summary),
        "summary_preview": summary[:200],
        "engagement_ids": row.get("engagement_ids") or [],
        "source": row.get("source", "calendar"),
    }
