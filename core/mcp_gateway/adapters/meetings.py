"""MCP meetings-Adapter — Kalender-Sync in Meeting-Inbox."""

from __future__ import annotations

from typing import Any

from core.google.meetings.sync import sync_calendar_to_inbox
from core.mcp_gateway.adapters.registry import register
from core.orchestrator.meetings_store import (
    compute_person_meeting_stats,
    lookup_person_meeting_stats,
)


@register("meetings", "sync_from_calendar")
def meetings_sync_from_calendar(args: dict[str, Any]) -> dict[str, Any]:
    tenant_id = str(args.get("tenant_id") or "nextchapter")
    return sync_calendar_to_inbox(
        tenant_id=tenant_id,
        since_date=args.get("since_date"),
        until_date=args.get("until_date"),
        include_forecast=bool(args.get("include_forecast", True)),
        forecast_days=int(args.get("forecast_days") or 31),
        dry_run=bool(args.get("dry_run", True)),
        max_events=int(args.get("max_events") or 500),
    )


@register("meetings", "person_stats")
def meetings_person_stats(args: dict[str, Any]) -> dict[str, Any]:
    tenant_id = str(args.get("tenant_id") or "nextchapter")
    since_date = args.get("since_date")
    person = args.get("person") or args.get("email") or args.get("name")
    if person:
        stat = lookup_person_meeting_stats(
            tenant_id,
            str(person),
            since_date=str(since_date) if since_date else None,
        )
        return {
            "ok": True,
            "found": stat is not None,
            "person": stat,
        }
    stats = compute_person_meeting_stats(
        tenant_id,
        since_date=str(since_date) if since_date else None,
    )
    return {"ok": True, "count": len(stats), "person_stats": stats}


@register("meetings", "status")
def meetings_status(args: dict[str, Any]) -> dict[str, Any]:
    from core.google import auth as google_auth

    return {
        "ok": True,
        "calendar_configured": google_auth.secrets_configured(),
        "default_since_date": "2026-07-01",
    }


@register("meetings", "commit_to_company_brain")
def meetings_commit_to_company_brain(args: dict[str, Any]) -> dict[str, Any]:
    from core.orchestrator.dataproducts import OrgMeeting
    from core.orchestrator.dp_service import commit_dataproduct, DPCommitError
    from core.orchestrator.meetings_store import get_meeting, update_meeting

    tenant_id = str(args.get("tenant_id") or "nextchapter")
    meeting_id = str(args.get("meeting_id") or "").strip()
    summary = str(args.get("summary") or "").strip()
    dry_run = bool(args.get("dry_run", True))

    if not meeting_id:
        return {"ok": False, "error": "missing_meeting_id", "message": "meeting_id erforderlich"}
    if not summary:
        return {"ok": False, "error": "missing_summary", "message": "Zusammenfassung erforderlich"}

    meeting = get_meeting(meeting_id, tenant_id)
    if not meeting:
        return {"ok": False, "error": "meeting_not_found", "message": f"Meeting {meeting_id} nicht gefunden"}

    attendee_refs: list[str] = []
    for ref in meeting.get("participant_refs") or []:
        if isinstance(ref, dict):
            email = str(ref.get("email") or "").strip()
            if email:
                attendee_refs.append(email)

    external_id = meeting_id
    org_meeting = OrgMeeting(
        tenant_id=tenant_id,
        produced_by="meetings-agent",
        meeting_id=external_id,
        title=str(meeting.get("title") or ""),
        held_at=str(meeting.get("held_at") or ""),
        summary=summary,
        attendee_refs=attendee_refs,
        source_ref=str(meeting.get("calendar_event_id") or meeting_id),
        about_refs=list(meeting.get("engagement_ids") or []),
    )

    if dry_run:
        preview = commit_dataproduct(org_meeting, dry_run=True)
        return {
            "ok": True,
            "dry_run": True,
            "meeting_id": meeting_id,
            "kg_node_type": preview.get("node_type", "org:Meeting"),
            "kg_external_id": preview.get("external_id", external_id),
            "summary": (
                f"Dry-Run: Würde org:Meeting '{meeting.get('title')}' "
                f"mit Zusammenfassung ({len(summary)} Zeichen) committen."
            ),
        }

    update_meeting(meeting_id, tenant_id, {"summary": summary})
    try:
        result = commit_dataproduct(org_meeting, dry_run=False)
    except DPCommitError as exc:
        return {"ok": False, "error": "commit_failed", "message": str(exc)}

    return {
        "ok": True,
        "dry_run": False,
        "meeting_id": meeting_id,
        "kg_node_type": result.get("node_type", "org:Meeting"),
        "kg_external_id": result.get("external_id", external_id),
        "kg_node_id": str(result.get("node_id") or ""),
        "summary": f"Meeting '{meeting.get('title')}' im Company Brain gespeichert (org:Meeting).",
    }
