"""Email-Agent DataProducts (email:*) — Roadmap §9.3."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sdk.dataproduct import DataProduct


class InvoiceRecord(DataProduct):
    """Einzelne Rechnung — entspricht Sheet-Zeile + Metadaten."""

    vendor: str = ""
    purpose: str = ""
    amount: str = ""
    interval: str = ""
    contract_start: str = ""
    next_renewal: str = ""
    cancellation_days: str = ""
    last_cancel_date: str = ""
    payment_method: str = ""
    invoice_id: str = ""
    status: str = "Prüfen"
    source_message_id: str = ""
    drive_url: str = ""
    drive_path: str = ""


class InvoiceRunRequest(DataProduct):
    """Input: Rechnungs-Pipeline starten (Agent-intern)."""

    dry_run: bool = Field(
        default=True,
        description="Dry-Run: Gmail scannen ohne Sheet/Drive zu beschreiben",
    )
    skip_archive: bool = Field(
        default=False,
        description="PDF-Archivierung in Google Drive überspringen",
    )
    storage_target: list[str] = Field(default_factory=lambda: ["G"])


class InvoiceRunUserInput(BaseModel):
    """Console-UI: nur Felder, die Nutzer verstehen und setzen müssen."""

    model_config = ConfigDict(
        json_schema_extra={
            "title": "Gmail-Rechnungen extrahieren",
            "description": (
                "Gmail nach Rechnungen durchsuchen, neue Einträge ins Google Sheet schreiben "
                "und PDFs optional in Google Drive ablegen."
            ),
        }
    )

    run_mode: Literal["dry_run", "live"] = Field(
        default="dry_run",
        title="Ausführungsmodus",
        description="Dry-Run prüft Kandidaten ohne Sheet oder Drive zu verändern.",
        json_schema_extra={
            "x-enum-labels": {
                "dry_run": "Nur Vorschau (Dry-Run) — nichts schreiben",
                "live": "Live — Sheet & Drive aktualisieren",
            }
        },
    )
    archive_mode: Literal["archive", "skip"] = Field(
        default="archive",
        title="PDF-Archiv in Drive",
        description="Rechnungs-PDFs in den Google-Drive-Ordner „Rechnungen“ ablegen.",
        json_schema_extra={
            "x-enum-labels": {
                "archive": "PDFs nach Drive archivieren",
                "skip": "Archivierung überspringen",
            }
        },
    )

    def to_agent_request(
        self,
        *,
        tenant_id: str = "nextchapter",
        produced_by: str = "email-agent",
    ) -> InvoiceRunRequest:
        return InvoiceRunRequest(
            tenant_id=tenant_id,
            produced_by=produced_by,
            dry_run=self.run_mode == "dry_run",
            skip_archive=self.archive_mode == "skip",
        )


class InvoicePipelineReport(DataProduct):
    """Output: Ergebnis Extract → Archive → Sheet."""

    candidates: int = 0
    written: int = 0
    archived: int = 0
    pdf_found: int = 0
    labeled: int = 0
    updated_links: int = 0
    sheet_url: str = ""
    sheet_name: str = ""
    spreadsheet_id: str = ""
    dry_run: bool = False
    invoices: list[InvoiceRecord] = Field(default_factory=list)
    summary: str = ""
    pii_cleared: bool = False
    storage_target: list[str] = Field(default_factory=lambda: ["G"])


class InvoiceExportRequest(DataProduct):
    """Input: Steuer-Export nach lokalem Verzeichnis."""

    tax_year: int = Field(default=2025, description="Steuerjahr für den Export")
    dest: str = Field(default="", description="Zielverzeichnis (leer = Standard aus Konfiguration)")
    dry_run: bool = Field(default=True, description="Dry-Run: nur zählen, nichts schreiben")
    storage_target: list[str] = Field(default_factory=lambda: ["G", "K"])


class InvoiceExport(DataProduct):
    """Output: Steuer-Export — Roadmap §9.3."""

    tax_year: int
    total_amount: float = 0.0
    export_format: Literal["csv", "json", "xlsx"] = "json"
    messages: int = 0
    exported: int = 0
    exported_pdf: int = 0
    exported_eml: int = 0
    skipped_year: int = 0
    skipped_empty: int = 0
    vendors: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    dest: str = ""
    dry_run: bool = False
    pii_cleared: bool = False
    summary: str = ""
    storage_target: list[str] = Field(default_factory=lambda: ["G", "K"])
