"""Email-Agent — Rechnungs-Pipeline via MCP (P5/P8)."""

from __future__ import annotations

from agents.email.dataproducts import (
    InvoiceExport,
    InvoiceExportRequest,
    InvoicePipelineReport,
    InvoiceRecord,
    InvoiceRunRequest,
)
from core.orchestrator.pii_redactor import redact_pii
from sdk.agent_base import AgentBase


class EmailAgent(AgentBase[InvoiceRunRequest, InvoicePipelineReport]):
    agent_id = "email-agent"
    version = "1.0.0"
    input_schema = InvoiceRunRequest
    output_schema = InvoicePipelineReport

    async def run(self, input_dp: InvoiceRunRequest) -> InvoicePipelineReport:
        result = await self.mcp.call(
            "mail",
            "run_invoices",
            {
                "dry_run": input_dp.dry_run,
                "skip_archive": input_dp.skip_archive,
                "tenant_id": input_dp.tenant_id,
            },
            timeout=300.0,
        )
        invoices = [
            InvoiceRecord(
                tenant_id=input_dp.tenant_id,
                produced_by=self.agent_id,
                vendor=str(inv.get("vendor") or ""),
                purpose=str(inv.get("purpose") or ""),
                amount=str(inv.get("amount") or ""),
                interval=str(inv.get("interval") or ""),
                contract_start=str(inv.get("contract_start") or ""),
                next_renewal=str(inv.get("next_renewal") or ""),
                cancellation_days=str(inv.get("cancellation_days") or ""),
                last_cancel_date=str(inv.get("last_cancel_date") or ""),
                payment_method=str(inv.get("payment_method") or ""),
                invoice_id=str(inv.get("invoice_id") or ""),
                status=str(inv.get("status") or "Prüfen"),
                source_message_id=str(inv.get("source_message_id") or ""),
                drive_url=str(inv.get("drive_url") or ""),
                drive_path=str(inv.get("drive_path") or ""),
            )
            for inv in (result.get("invoices") or [])
        ]
        summary = _build_summary(result)
        redacted = redact_pii(summary)
        return InvoicePipelineReport(
            tenant_id=input_dp.tenant_id,
            produced_by=self.agent_id,
            candidates=int(result.get("candidates") or 0),
            written=int(result.get("written") or 0),
            archived=int(result.get("archived") or 0),
            pdf_found=int(result.get("pdf_found") or 0),
            labeled=int(result.get("labeled") or 0),
            updated_links=int(result.get("updated_links") or 0),
            sheet_url=str(result.get("sheet_url") or ""),
            sheet_name=str(result.get("sheet_name") or ""),
            spreadsheet_id=str(result.get("spreadsheet_id") or ""),
            dry_run=bool(result.get("dry_run")),
            invoices=invoices,
            summary=redacted.redacted_text,
            pii_cleared=redacted.pii_count > 0,
        )


class InvoiceExportAgent(AgentBase[InvoiceExportRequest, InvoiceExport]):
    """Steuer-Export — separates Intent/Workflow."""

    agent_id = "email-agent"
    version = "1.0.0"
    input_schema = InvoiceExportRequest
    output_schema = InvoiceExport

    async def run(self, input_dp: InvoiceExportRequest) -> InvoiceExport:
        result = await self.mcp.call(
            "mail",
            "export_steuer",
            {
                "year": input_dp.tax_year,
                "dest": input_dp.dest,
                "dry_run": input_dp.dry_run,
                "tenant_id": input_dp.tenant_id,
            },
        )
        files = [str(f) for f in (result.get("files") or [])]
        summary = (
            f"Steuer-Export {input_dp.tax_year}: {result.get('exported', 0)} Datei(en) "
            f"nach {result.get('dest', input_dp.dest)}"
        )
        redacted = redact_pii(summary)
        return InvoiceExport(
            tenant_id=input_dp.tenant_id,
            produced_by=self.agent_id,
            tax_year=input_dp.tax_year,
            messages=int(result.get("messages") or 0),
            exported=int(result.get("exported") or 0),
            exported_pdf=int(result.get("exported_pdf") or 0),
            exported_eml=int(result.get("exported_eml") or 0),
            skipped_year=int(result.get("skipped_year") or 0),
            skipped_empty=int(result.get("skipped_empty") or 0),
            vendors=list(result.get("vendors") or []),
            files=files,
            dest=str(result.get("dest") or input_dp.dest),
            dry_run=bool(result.get("dry_run")),
            pii_cleared=redacted.pii_count > 0,
            summary=redacted.redacted_text,
        )


def _build_summary(result: dict) -> str:
    mode = "Dry-Run" if result.get("dry_run") else "Live"
    lines = [
        f"Rechnungs-Pipeline ({mode})",
        f"Kandidaten: {result.get('candidates', 0)} | Neu im Sheet: {result.get('written', 0)}",
    ]
    if result.get("archived"):
        lines.append(f"Archiviert: {result['archived']} (PDFs: {result.get('pdf_found', 0)})")
    if result.get("sheet_url"):
        lines.append(f"Sheet: {result['sheet_url']}")
    return "\n".join(lines)


async def run_invoice_export(input_dp: InvoiceExportRequest, **agent_kwargs) -> InvoiceExport:
    agent = InvoiceExportAgent(**agent_kwargs)
    return await agent.execute(input_dp)
