"""Rechnungs-Pipeline — Gmail → PDF-Text/OCR → Drive → Sheet (deterministisch, kein LLM)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from core.google import auth
from core.google.gmail_client import mark_messages_processed
from core.google.invoice.archive import archive_message_pdfs
from core.google.invoice.config import load_invoice_config
from core.google.invoice.enrich import collect_message_pdf_text, combine_extraction_text
from core.google.invoice.extract import (
    SHEET_NAME,
    InvoiceRow,
    fetch_invoice_messages,
    find_first_empty_row,
    merge_invoice_rows,
    message_to_invoice_row,
    read_existing_invoice_ids,
    resolve_gmail_queries,
    update_drive_urls,
    write_rows,
)
from core.google.invoice.mime import collect_pdf_attachments, pdfs_from_parsed_message
from core.google.scopes import scope_urls

_PIPELINE_SCOPES = scope_urls(["gmail.readonly", "spreadsheets", "drive"])


def _pipeline_cfg(config: dict) -> dict:
    return config.get("pipeline") or {}


def _gmail_cfg(config: dict) -> dict:
    return config.get("gmail") or {}


def _pdf_ocr_enabled(config: dict) -> bool:
    return bool(_pipeline_cfg(config).get("pdf_ocr_fallback", True))


def _build_services(*, interactive: bool = False):
    from googleapiclient.discovery import build

    creds = auth.load_credentials(_PIPELINE_SCOPES, "token.json", interactive=interactive)
    gmail = build("gmail", "v1", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return gmail, sheets, drive, creds


def run_invoice_pipeline(
    *,
    tenant_id: str = "nextchapter",
    dry_run: bool = False,
    skip_archive: bool = False,
    interactive: bool = False,
) -> dict[str, Any]:
    """Orchestriert Extract → Archive → Sheet → Label."""
    config = load_invoice_config(tenant_id)
    spreadsheet_id = config.get("spreadsheet_id", "")
    gmail_cfg = _gmail_cfg(config)
    processed_label = gmail_cfg.get("processed_label", "R-Verarbeitet")
    skip_processed = gmail_cfg.get("skip_processed", True)
    full_inbox = gmail_cfg.get("full_inbox_scan", True)
    reprocess_if_pdfs = gmail_cfg.get("reprocess_if_pdfs_remain", True)
    label_after_run = _pipeline_cfg(config).get("label_after_run", True)
    pdf_ocr = _pdf_ocr_enabled(config)

    gmail, sheets, drive, _creds = _build_services(interactive=interactive)

    messages = fetch_invoice_messages(
        gmail,
        full_inbox=full_inbox,
        processed_label=processed_label,
        skip_processed=skip_processed,
        reprocess_if_pdfs_remain=reprocess_if_pdfs,
        gmail_queries=resolve_gmail_queries(config),
        pdf_ocr=pdf_ocr,
    )
    rows = [message_to_invoice_row(m) for m in messages]

    archived = 0
    pdf_found = 0
    label_ids: list[str] = []

    if not skip_archive:
        msg_by_id = {m["id"]: m for m in messages}
        enriched: list[InvoiceRow] = []
        for row in rows:
            msg = msg_by_id.get(row.source_message_id, {})
            payload = msg.get("payload", {})
            parsed_eml = msg.get("parsed_eml")
            parent_id = msg.get("parent_id") or row.source_message_id
            if dry_run:
                if parsed_eml is not None:
                    n = len(pdfs_from_parsed_message(parsed_eml))
                else:
                    n = len(collect_pdf_attachments(gmail, row.source_message_id, payload))
                if n:
                    pdf_found += n
                enriched.append(row)
                continue
            result = archive_message_pdfs(
                gmail,
                drive,
                row.source_message_id,
                payload,
                vendor=row.vendor,
                invoice_id=row.invoice_id,
                date_str=row.contract_start,
                config=config,
                parsed_eml=parsed_eml,
            )
            if result:
                archived += 1
                pdf_found += int(result.get("pdf_count") or 1)
                row = replace(
                    row,
                    drive_url=result.get("drive_url", ""),
                    drive_path=result.get("drive_path", ""),
                )
                label_ids.append(parent_id)
            else:
                if parsed_eml is not None:
                    remaining = len(pdfs_from_parsed_message(parsed_eml))
                else:
                    remaining = len(collect_pdf_attachments(gmail, row.source_message_id, payload))
                if remaining == 0:
                    label_ids.append(parent_id)
            enriched.append(row)
        rows = enriched

    rows = merge_invoice_rows(rows)
    if dry_run:
        new_rows = rows
        existing_ids: set[str] = set()
    else:
        existing_ids = read_existing_invoice_ids(sheets, spreadsheet_id=spreadsheet_id)
        new_rows = [r for r in rows if not r.invoice_id or r.invoice_id not in existing_ids]

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "candidates": len(rows),
            "written": len(new_rows),
            "new_rows": len(new_rows),
            "pdf_found": pdf_found if not skip_archive else 0,
            "spreadsheet_id": spreadsheet_id,
            "invoices": [_row_to_dict(r) for r in new_rows],
        }

    updated_links = update_drive_urls(sheets, rows, spreadsheet_id=spreadsheet_id)
    start_row = 0
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit" if spreadsheet_id else ""

    if new_rows:
        start_row = find_first_empty_row(sheets, spreadsheet_id=spreadsheet_id)
        write_rows(sheets, start_row, new_rows, spreadsheet_id=spreadsheet_id)

    labeled = 0
    if label_after_run and label_ids:
        try:
            labeled = mark_messages_processed(
                list(dict.fromkeys(label_ids)),
                label_name=processed_label,
                interactive=interactive,
            )
        except Exception:
            labeled = 0

    return {
        "ok": True,
        "dry_run": False,
        "candidates": len(rows),
        "written": len(new_rows),
        "updated_links": updated_links,
        "archived": archived if not skip_archive else 0,
        "pdf_found": pdf_found if not skip_archive else 0,
        "labeled": labeled,
        "start_row": start_row,
        "sheet_url": sheet_url,
        "sheet_name": config.get("sheet_name", SHEET_NAME),
        "processed_label": processed_label,
        "spreadsheet_id": spreadsheet_id,
        "invoices": [_row_to_dict(r) for r in new_rows],
    }


def preview_invoices(*, tenant_id: str = "nextchapter", interactive: bool = False) -> dict[str, Any]:
    """Nur Extract — keine Side-Effects."""
    config = load_invoice_config(tenant_id)
    gmail_cfg = _gmail_cfg(config)
    from googleapiclient.discovery import build

    creds = auth.load_for_tool("mail", "preview_invoices", interactive=interactive)
    gmail = build("gmail", "v1", credentials=creds)
    messages = fetch_invoice_messages(
        gmail,
        full_inbox=gmail_cfg.get("full_inbox_scan", True),
        processed_label=gmail_cfg.get("processed_label", "R-Verarbeitet"),
        skip_processed=gmail_cfg.get("skip_processed", True),
        reprocess_if_pdfs_remain=gmail_cfg.get("reprocess_if_pdfs_remain", True),
        gmail_queries=resolve_gmail_queries(config),
        pdf_ocr=_pdf_ocr_enabled(config),
    )
    rows = merge_invoice_rows([message_to_invoice_row(m) for m in messages])
    return {
        "ok": True,
        "count": len(rows),
        "invoices": [_row_to_dict(r) for r in rows],
    }


def _row_to_dict(row: InvoiceRow) -> dict[str, Any]:
    return {
        "vendor": row.vendor,
        "purpose": row.purpose,
        "amount": row.amount,
        "interval": row.interval,
        "contract_start": row.contract_start,
        "next_renewal": row.next_renewal,
        "cancellation_days": row.cancellation_days,
        "last_cancel_date": row.last_cancel_date,
        "payment_method": row.payment_method,
        "invoice_id": row.invoice_id,
        "status": row.status,
        "source_message_id": row.source_message_id,
        "drive_url": row.drive_url,
        "drive_path": row.drive_path,
    }
