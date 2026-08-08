"""Meetings-Agent DataProducts — Kalender, Zusammenfassung, Company Brain."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sdk.dataproduct import DataProduct


class MeetingAttendee(DataProduct):
    email: str = ""
    name: str = ""


class MeetingRecord(DataProduct):
    meeting_id: str = ""
    calendar_event_id: str = ""
    project: str = ""
    title: str = ""
    held_at: str = ""
    end_at: str = ""
    location: str = ""
    attendees: list[MeetingAttendee] = Field(default_factory=list)
    has_summary: bool = False
    summary_preview: str = ""
    participants_label: str = ""


class PersonMeetingStats(DataProduct):
    email: str = ""
    name: str = ""
    meeting_count: int = 0
    first_meeting_at: str = ""
    last_meeting_at: str = ""
    meeting_ids: list[str] = Field(default_factory=list)
    meeting_titles: list[str] = Field(default_factory=list)


class ForecastMeeting(DataProduct):
    held_at: str = ""
    project: str = ""
    title: str = ""
    location: str = ""
    participants_label: str = ""
    attendee_emails: list[str] = Field(default_factory=list)
    calendar_event_id: str = ""


class MeetingsAgentRequest(DataProduct):
    operation: Literal["termine_abrufen", "zusammenfassung_speichern"] = "termine_abrufen"
    since_date: str = "2026-07-01"
    include_forecast: bool = True
    meeting_id: str = ""
    summary: str = ""
    dry_run: bool = True
    storage_target: list[str] = Field(default_factory=lambda: ["G"])


class MeetingsAgentUserInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "title": "Meetings-Agent",
            "description": (
                "Termine aus Google-Kalender laden (ab 1. Juli 2026) oder "
                "Meeting-Zusammenfassung ins Company Brain speichern."
            ),
        }
    )

    aufgabe: Literal["termine_abrufen", "zusammenfassung_speichern"] = Field(
        default="termine_abrufen",
        title="Aufgabe",
        json_schema_extra={
            "x-enum-labels": {
                "termine_abrufen": "Termine aus Kalender laden",
                "zusammenfassung_speichern": "Zusammenfassung ins Company Brain",
            }
        },
    )
    run_mode: Literal["dry_run", "live"] = Field(
        default="dry_run",
        title="Ausführungsmodus",
        json_schema_extra={
            "x-enum-labels": {
                "dry_run": "Nur Vorschau (Dry-Run)",
                "live": "Live ausführen",
            }
        },
    )
    since_date: str = Field(
        default="2026-07-01",
        title="Kalender ab Datum",
        json_schema_extra={"x-visible-when": {"aufgabe": "termine_abrufen"}},
    )
    include_forecast: Literal["yes", "no"] = Field(
        default="yes",
        title="Forecast (31 Tage)",
        json_schema_extra={
            "x-enum-labels": {"yes": "Ja", "no": "Nein"},
            "x-visible-when": {"aufgabe": "termine_abrufen"},
        },
    )
    meeting_id: str = Field(
        default="",
        title="Meeting auswählen",
        description="Termin mit Titel, Datum und Teilnehmern — nicht nur die technische ID",
        json_schema_extra={
            "x-visible-when": {"aufgabe": "zusammenfassung_speichern"},
            "x-widget": "meeting-picker",
        },
    )
    summary: str = Field(
        default="",
        title="Zusammenfassung",
        json_schema_extra={
            "x-visible-when": {"aufgabe": "zusammenfassung_speichern"},
            "x-widget": "textarea",
        },
    )

    @model_validator(mode="after")
    def _validate_summary_task(self) -> "MeetingsAgentUserInput":
        if self.aufgabe == "zusammenfassung_speichern":
            if not self.meeting_id.strip():
                raise ValueError("Bitte ein Meeting aus der Liste wählen.")
            if not self.summary.strip():
                raise ValueError("Bitte eine Zusammenfassung eingeben.")
        return self

    def to_agent_request(
        self,
        *,
        tenant_id: str = "nextchapter",
        produced_by: str = "meetings-agent",
    ) -> MeetingsAgentRequest:
        return MeetingsAgentRequest(
            tenant_id=tenant_id,
            produced_by=produced_by,
            operation=self.aufgabe,
            since_date=self.since_date,
            include_forecast=self.include_forecast == "yes",
            meeting_id=self.meeting_id.strip(),
            summary=self.summary.strip(),
            dry_run=self.run_mode == "dry_run",
        )

    @classmethod
    def get_ui_schema(cls) -> dict:
        return cls.model_json_schema()


class MeetingsAgentReport(DataProduct):
    operation: str = ""
    since_date: str = ""
    until_date: str = ""
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    dry_run: bool = False
    meetings: list[MeetingRecord] = Field(default_factory=list)
    person_stats: list[PersonMeetingStats] = Field(default_factory=list)
    forecast_next_month: list[ForecastMeeting] = Field(default_factory=list)
    discovered_projects: list[str] = Field(default_factory=list)
    committed_meeting_id: str = ""
    kg_node_type: str = ""
    kg_external_id: str = ""
    summary: str = ""
    storage_target: list[str] = Field(default_factory=lambda: ["G"])
