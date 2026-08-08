"""Meetings-Fachagent — Kalender & Company Brain via MCP (P5/P8)."""

from __future__ import annotations

from agents.meetings.dataproducts import (
    ForecastMeeting,
    MeetingAttendee,
    MeetingRecord,
    MeetingsAgentReport,
    MeetingsAgentRequest,
    PersonMeetingStats,
)
from sdk.agent_base import AgentBase


class MeetingsAgent(AgentBase[MeetingsAgentRequest, MeetingsAgentReport]):
    agent_id = "meetings-agent"
    version = "2.0.0"
    input_schema = MeetingsAgentRequest
    output_schema = MeetingsAgentReport

    async def run(self, input_dp: MeetingsAgentRequest) -> MeetingsAgentReport:
        if input_dp.operation == "zusammenfassung_speichern":
            result = await self.mcp.call(
                "meetings",
                "commit_to_company_brain",
                {
                    "tenant_id": input_dp.tenant_id,
                    "meeting_id": input_dp.meeting_id,
                    "summary": input_dp.summary,
                    "dry_run": input_dp.dry_run,
                },
                timeout=120.0,
            )
            return self._report_commit(input_dp, result)

        result = await self.mcp.call(
            "meetings",
            "sync_from_calendar",
            {
                "tenant_id": input_dp.tenant_id,
                "since_date": input_dp.since_date,
                "include_forecast": input_dp.include_forecast,
                "dry_run": input_dp.dry_run,
            },
            timeout=180.0,
        )
        return self._report_sync(input_dp, result)

    def _report_sync(self, input_dp: MeetingsAgentRequest, result: dict) -> MeetingsAgentReport:
        if not result.get("ok", True) and result.get("error"):
            return MeetingsAgentReport(
                tenant_id=input_dp.tenant_id,
                produced_by=self.agent_id,
                operation="termine_abrufen",
                since_date=input_dp.since_date,
                summary=str(result.get("message") or result.get("error")),
                dry_run=input_dp.dry_run,
            )
        meetings = [
            MeetingRecord(
                tenant_id=input_dp.tenant_id,
                produced_by=self.agent_id,
                meeting_id=str(m.get("meeting_id") or ""),
                calendar_event_id=str(m.get("calendar_event_id") or ""),
                project=str(m.get("project") or ""),
                title=str(m.get("title") or ""),
                held_at=str(m.get("held_at") or ""),
                end_at=str(m.get("end_at") or ""),
                location=str(m.get("location") or ""),
                attendees=[
                    MeetingAttendee(
                        tenant_id=input_dp.tenant_id,
                        produced_by=self.agent_id,
                        email=str(a.get("email") or ""),
                        name=str(a.get("name") or ""),
                    )
                    for a in (m.get("attendees") or [])
                ],
                has_summary=bool(m.get("has_summary")),
                summary_preview=str(m.get("summary_preview") or "")[:200],
                participants_label=str(m.get("participants_label") or ""),
            )
            for m in (result.get("meetings") or [])
        ]
        person_stats = [
            PersonMeetingStats(
                tenant_id=input_dp.tenant_id,
                produced_by=self.agent_id,
                email=str(p.get("email") or ""),
                name=str(p.get("name") or ""),
                meeting_count=int(p.get("meeting_count") or 0),
                first_meeting_at=str(p.get("first_meeting_at") or ""),
                last_meeting_at=str(p.get("last_meeting_at") or ""),
                meeting_ids=list(p.get("meeting_ids") or []),
                meeting_titles=list(p.get("meeting_titles") or []),
            )
            for p in (result.get("person_stats") or [])
        ]
        forecast = [
            ForecastMeeting(
                tenant_id=input_dp.tenant_id,
                produced_by=self.agent_id,
                held_at=str(f.get("held_at") or ""),
                project=str(f.get("project") or ""),
                title=str(f.get("title") or ""),
                location=str(f.get("location") or ""),
                participants_label=str(f.get("participants_label") or ""),
                attendee_emails=list(f.get("attendee_emails") or []),
                calendar_event_id=str(f.get("calendar_event_id") or ""),
            )
            for f in (result.get("forecast_next_month") or [])
        ]
        return MeetingsAgentReport(
            tenant_id=input_dp.tenant_id,
            produced_by=self.agent_id,
            operation="termine_abrufen",
            since_date=str(result.get("since_date") or input_dp.since_date),
            until_date=str(result.get("until_date") or ""),
            imported=int(result.get("imported") or 0),
            updated=int(result.get("updated") or 0),
            skipped=int(result.get("skipped") or 0),
            dry_run=bool(result.get("dry_run", input_dp.dry_run)),
            meetings=meetings,
            person_stats=person_stats,
            forecast_next_month=forecast,
            discovered_projects=list(result.get("discovered_projects") or []),
            summary=str(result.get("summary") or ""),
        )

    def _report_commit(self, input_dp: MeetingsAgentRequest, result: dict) -> MeetingsAgentReport:
        if not result.get("ok", True):
            return MeetingsAgentReport(
                tenant_id=input_dp.tenant_id,
                produced_by=self.agent_id,
                operation="zusammenfassung_speichern",
                committed_meeting_id=input_dp.meeting_id,
                dry_run=input_dp.dry_run,
                summary=str(result.get("message") or result.get("error") or "Fehler"),
            )
        return MeetingsAgentReport(
            tenant_id=input_dp.tenant_id,
            produced_by=self.agent_id,
            operation="zusammenfassung_speichern",
            dry_run=bool(result.get("dry_run", input_dp.dry_run)),
            committed_meeting_id=str(result.get("meeting_id") or input_dp.meeting_id),
            kg_node_type=str(result.get("kg_node_type") or "org:Meeting"),
            kg_external_id=str(result.get("kg_external_id") or ""),
            summary=str(result.get("summary") or ""),
        )
