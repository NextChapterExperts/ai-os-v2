"""Backfill — Drive-PDFs einlesen (pypdf/OCR) und Google-Sheet-Zeilen anreichern."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from core.google import auth
from core.google.invoice.config import load_invoice_config
from core.google.invoice.drive_inventory import (
    download_pdf_bytes,
    iter_drive_pdfs,
    resolve_invoice_root_folder_id,
)
from core.google.invoice.extract import (
    DATA_START_ROW,
    SHEET_NAME,
    InvoiceRow,
    extract_amount,
    extract_cancellation_days,
    extract_contract_date,
    extract_invoice_id,
    extract_next_renewal,
    extract_payment_method,
    extract_purpose,
    find_first_empty_row,
    infer_interval,
    infer_vendor,
    write_rows,
)
from core.google.invoice.pdf_text import extract_text_from_pdf_bytes
from core.google.scopes import scope_urls

_SHEET_SCOPES = scope_urls(["spreadsheets", "drive"])

_FILENAME_HINT = re.compile(
    r"^(?P<vendor>.+)_(?P<invoice_id>[^_]+)_(?P<date>\d{4}-\d{2}-\d{2})(?:_\d+)?\.pdf$",
    re.IGNORECASE,
)


@dataclass
class SheetRow:
    row_num: int
    values: list[str]

    @property
    def vendor(self) -> str:
        return _cell(self.values, 0)

    @property
    def purpose(self) -> str:
        return _cell(self.values, 1)

    @property
    def amount(self) -> str:
        return _cell(self.values, 2)

    @property
    def contract_start(self) -> str:
        return _cell(self.values, 4)

    @property
    def invoice_id(self) -> str:
        return _cell(self.values, 9)

    @property
    def drive_url(self) -> str:
        return _cell(self.values, 11)


def _cell(row: list[str], index: int) -> str:
    if index >= len(row):
        return ""
    return str(row[index]).strip()


def _pad_row(values: list[str]) -> list[str]:
    padded = list(values)
    while len(padded) < 12:
        padded.append("")
    return padded[:12]


def parse_filename_hints(filename: str) -> dict[str, str]:
    """Aus Archiv-Dateiname {vendor}_{invoice_id}_{date}.pdf Metadaten lesen."""
    match = _FILENAME_HINT.match(filename.strip())
    if not match:
        return {}
    vendor = match.group("vendor").replace("_", " ").strip()
    invoice_id = match.group("invoice_id").strip()
    if invoice_id.lower() in {"ohne", "ohne_nr", "none", "na"}:
        invoice_id = ""
    date_raw = match.group("date")
    contract_start = ""
    if date_raw:
        parts = date_raw.split("-")
        if len(parts) == 3:
            contract_start = f"{parts[2]}.{parts[1]}.{parts[0]}"
    return {
        "vendor": vendor,
        "invoice_id": invoice_id,
        "contract_start": contract_start,
        "subject": f"Rechnung {vendor}",
    }


def pdf_to_invoice_row(
    *,
    filename: str,
    drive_path: str,
    drive_url: str,
    file_id: str,
    pdf_bytes: bytes,
    ocr: bool = True,
) -> InvoiceRow:
    """PDF → InvoiceRow mit gleicher Parser-/OCR-Pipeline wie Gmail-Agent."""
    hints = parse_filename_hints(filename)
    pdf_text = extract_text_from_pdf_bytes(pdf_bytes, ocr=ocr)
    subject = hints.get("subject") or f"Rechnung {filename}"
    text = pdf_text

    invoice_id = hints.get("invoice_id") or extract_invoice_id(text, subject)
    vendor_hint = hints.get("vendor") or ""

    return InvoiceRow(
        vendor=vendor_hint or infer_vendor(subject, "", text),
        purpose=extract_purpose(text, subject),
        amount=extract_amount(text, strict=True) or extract_amount(text, strict=False),
        interval=infer_interval(text, subject),
        contract_start=hints.get("contract_start")
        or extract_contract_date(text, ""),
        next_renewal=extract_next_renewal(text),
        cancellation_days=extract_cancellation_days(text),
        last_cancel_date="",
        payment_method=extract_payment_method(text),
        invoice_id=invoice_id,
        status="Prüfen",
        source_message_id=f"drive:{file_id}",
        drive_url=drive_url,
        drive_path=drive_path,
    )


def enrich_sheet_values(
    existing: list[str],
    extracted: InvoiceRow,
    *,
    force: bool = False,
) -> tuple[list[str], bool]:
    """Leere Sheet-Zellen aus Extraktion füllen (oder mit --force überschreiben)."""
    cols = _pad_row(existing)
    new_vals = extracted.to_sheet_row()
    changed = False
    for idx, new_val in enumerate(new_vals):
        new_val = str(new_val or "").strip()
        if not new_val:
            continue
        old_val = str(cols[idx] or "").strip()
        if force or not old_val:
            if old_val != new_val:
                cols[idx] = new_val
                changed = True
    return cols, changed


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _drive_id_from_url(url: str) -> str:
    for pattern in (
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def match_sheet_row(
    sheet_rows: list[SheetRow],
    *,
    file_id: str,
    drive_url: str,
    invoice_id: str,
    vendor: str,
    drive_path: str,
) -> SheetRow | None:
    """Bestehende Zeile finden: Drive-Link → Rechnungs-Nr. → Vendor+Pfad."""
    file_id = file_id.strip()
    invoice_id = invoice_id.strip()
    vendor_key = _normalize_key(vendor)

    for row in sheet_rows:
        row_url = row.drive_url
        if row_url and file_id and file_id in row_url:
            return row
        if drive_url and row_url and _normalize_key(row_url) == _normalize_key(drive_url):
            return row
        row_drive_id = _drive_id_from_url(row_url)
        if row_drive_id and row_drive_id == file_id:
            return row

    if invoice_id:
        for row in sheet_rows:
            if row.invoice_id and row.invoice_id.strip() == invoice_id:
                return row

    if vendor_key:
        path_tail = drive_path.split("/")[-1].lower()
        for row in sheet_rows:
            if _normalize_key(row.vendor) == vendor_key and not row.drive_url:
                if vendor_key.replace(" ", "_") in path_tail:
                    return row
    return None


def read_sheet_rows(sheets_service, *, spreadsheet_id: str) -> list[SheetRow]:
    range_name = f"{SHEET_NAME}!A{DATA_START_ROW}:L"
    result = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    rows: list[SheetRow] = []
    for idx, values in enumerate(result.get("values") or []):
        if not any(str(cell).strip() for cell in values):
            continue
        rows.append(SheetRow(row_num=DATA_START_ROW + idx, values=_pad_row(values)))
    return rows


def _build_services(*, interactive: bool = False):
    from googleapiclient.discovery import build

    creds = auth.load_credentials(
        _SHEET_SCOPES,
        "token.json",
        interactive=interactive,
        tool="invoice.backfill",
    )
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive, creds


def run_invoice_sheet_backfill(
    *,
    tenant_id: str = "nextchapter",
    dry_run: bool = False,
    force: bool = False,
    ocr: bool = True,
    limit: int | None = None,
    add_missing: bool = True,
    interactive: bool = False,
) -> dict[str, Any]:
    config = load_invoice_config(tenant_id)
    spreadsheet_id = str(config.get("spreadsheet_id") or "").strip()
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id fehlt in invoice.yaml")

    sheets, drive, _creds = _build_services(interactive=interactive)
    sheet_rows = read_sheet_rows(sheets, spreadsheet_id=spreadsheet_id)
    root_id, root_label = resolve_invoice_root_folder_id(config, drive)

    stats = {
        "ok": True,
        "dry_run": dry_run,
        "tenant_id": tenant_id,
        "spreadsheet_id": spreadsheet_id,
        "sheet_rows": len(sheet_rows),
        "pdfs_seen": 0,
        "pdfs_processed": 0,
        "rows_updated": 0,
        "rows_added": 0,
        "rows_unchanged": 0,
        "rows_unmatched_pdf": 0,
        "errors": 0,
        "updates": [],
        "additions": [],
    }

    batch_updates: list[dict] = []
    new_rows: list[InvoiceRow] = []

    for pdf_meta in iter_drive_pdfs(root_id, drive, root_label=root_label):
        stats["pdfs_seen"] += 1
        if limit is not None and stats["pdfs_processed"] >= limit:
            break

        file_id = pdf_meta["id"]
        filename = pdf_meta["name"]
        drive_url = pdf_meta.get("webViewLink") or ""
        drive_path = pdf_meta.get("drive_path") or filename

        try:
            pdf_bytes = download_pdf_bytes(file_id, drive)
            extracted = pdf_to_invoice_row(
                filename=filename,
                drive_path=drive_path,
                drive_url=drive_url,
                file_id=file_id,
                pdf_bytes=pdf_bytes,
                ocr=ocr,
            )
        except Exception as exc:
            stats["errors"] += 1
            stats["updates"].append({"file": filename, "error": str(exc)})
            continue

        stats["pdfs_processed"] += 1
        matched = match_sheet_row(
            sheet_rows,
            file_id=file_id,
            drive_url=drive_url,
            invoice_id=extracted.invoice_id,
            vendor=extracted.vendor,
            drive_path=drive_path,
        )

        if matched:
            merged, changed = enrich_sheet_values(matched.values, extracted, force=force)
            if changed:
                stats["rows_updated"] += 1
                stats["updates"].append(
                    {
                        "row": matched.row_num,
                        "file": filename,
                        "invoice_id": extracted.invoice_id or matched.invoice_id,
                        "vendor": extracted.vendor or matched.vendor,
                    }
                )
                if not dry_run:
                    batch_updates.append(
                        {
                            "range": f"{SHEET_NAME}!A{matched.row_num}:L{matched.row_num}",
                            "values": [merged],
                        }
                    )
                matched.values = merged
            else:
                stats["rows_unchanged"] += 1
        elif add_missing and (extracted.invoice_id or extracted.amount or extracted.vendor):
            stats["rows_added"] += 1
            stats["additions"].append(
                {
                    "file": filename,
                    "invoice_id": extracted.invoice_id,
                    "vendor": extracted.vendor,
                    "amount": extracted.amount,
                }
            )
            if not dry_run:
                new_rows.append(extracted)
        else:
            stats["rows_unmatched_pdf"] += 1

    if not dry_run:
        if batch_updates:
            sheets.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"valueInputOption": "USER_ENTERED", "data": batch_updates},
            ).execute()
        if new_rows:
            start_row = find_first_empty_row(sheets, spreadsheet_id=spreadsheet_id)
            write_rows(sheets, start_row, new_rows, spreadsheet_id=spreadsheet_id)

    return stats
