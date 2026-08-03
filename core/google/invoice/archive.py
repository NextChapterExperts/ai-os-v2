#!/usr/bin/env python3
"""Invoice-Archive-Agent — PDF-Anhänge (inkl. verschachtelter .eml) → Google Drive."""
from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path

from core.google import auth
from core.google.invoice.config import load_invoice_config
from core.google.invoice.mime import collect_pdf_attachments, pdfs_from_parsed_message
from googleapiclient.http import MediaIoBaseUpload

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
]


def _load_config() -> dict:
    return load_invoice_config()


def _safe_filename(text: str, max_len: int = 40) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", text.strip(), flags=re.UNICODE)
    return cleaned.strip("_")[:max_len] or "Rechnung"


def _find_or_create_folder(drive_service, name: str, parent_id: str | None = None) -> str:
    q = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    if parent_id:
        q += f" and '{parent_id}' in parents"
    else:
        q += " and 'root' in parents"
    result = drive_service.files().list(q=q, fields="files(id)", pageSize=1).execute()
    files = result.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    return drive_service.files().create(body=meta, fields="id").execute()["id"]


def _ensure_folder_path(drive_service, config: dict, date_str: str) -> tuple[str, str]:
    """Gibt (folder_id, relativer Pfad ab Rechnungen-Root) zurück."""
    drive_cfg = config.get("drive", {})
    root_name = drive_cfg.get("root_folder_name", "Rechnungen")
    root_id = drive_cfg.get("root_folder_id") or _find_or_create_folder(drive_service, root_name)

    path_tpl = (drive_cfg.get("path_template") or "").strip()
    if not path_tpl:
        return root_id, root_name

    try:
        if re.match(r"\d{2}\.\d{2}\.\d{4}", date_str):
            dt = datetime.strptime(date_str, "%d.%m.%Y")
        else:
            dt = datetime.now()
    except ValueError:
        dt = datetime.now()

    rel_suffix = path_tpl.format(year=dt.year, month=dt.month)
    parent = root_id
    for part in rel_suffix.split("/"):
        if part:
            parent = _find_or_create_folder(drive_service, part, parent)

    return parent, f"{root_name}/{rel_suffix}"


def archive_message_pdfs(
    gmail_service,
    drive_service,
    message_id: str,
    payload: dict,
    *,
    vendor: str,
    invoice_id: str,
    date_str: str,
    config: dict | None = None,
    parsed_eml=None,
) -> dict:
    """
    Lädt Rechnungs-PDFs nach Drive (direkt + aus verschachtelten .eml).
    Returns: {drive_url, drive_path, drive_file_id} oder leer.
    """
    config = config or _load_config()
    if parsed_eml is not None:
        pdfs = pdfs_from_parsed_message(parsed_eml)
    else:
        pdfs = collect_pdf_attachments(gmail_service, message_id, payload)
    if not pdfs:
        return {}

    folder_id, rel_base = _ensure_folder_path(drive_service, config, date_str)
    drive_cfg = config.get("drive", {})
    tpl = drive_cfg.get("filename_template", "{vendor}_{invoice_id}_{date}.pdf")

    safe_date = re.sub(r"[^\d]", "-", date_str)[:10] if date_str else datetime.now().strftime("%Y-%m-%d")
    base_fname = tpl.format(
        vendor=_safe_filename(vendor),
        invoice_id=_safe_filename(invoice_id or "ohne_nr"),
        date=safe_date,
    )
    if not base_fname.lower().endswith(".pdf"):
        base_fname += ".pdf"

    uploaded: list[dict] = []
    for idx, (orig_name, data) in enumerate(pdfs):
        if idx == 0:
            fname = base_fname
        else:
            stem = base_fname[:-4] if base_fname.lower().endswith(".pdf") else base_fname
            fname = f"{stem}_{idx + 1}.pdf"

        media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/pdf", resumable=False)
        created = drive_service.files().create(
            body={"name": fname, "parents": [folder_id]},
            media_body=media,
            fields="id, webViewLink",
        ).execute()
        uploaded.append({
            "drive_url": created.get("webViewLink", ""),
            "drive_path": f"{rel_base}/{fname}",
            "drive_file_id": created.get("id", ""),
            "source_filename": orig_name,
        })

    primary = uploaded[0]
    return {
        "drive_url": primary["drive_url"],
        "drive_path": primary["drive_path"],
        "drive_file_id": primary["drive_file_id"],
        "source_filename": primary["source_filename"],
        "pdf_count": len(uploaded),
        "drive_files": uploaded,
    }


def main() -> None:
    import argparse
    from extract_invoices_to_sheet import (
        fetch_invoice_messages,
        message_to_invoice_row,
    )

    parser = argparse.ArgumentParser(description="Invoice-Archive-Agent (Dry-Run)")
    parser.add_argument("--max", type=int, default=5, help="Max. Mails testen")
    args = parser.parse_args()

    creds = auth.load_credentials(SCOPES, "token.json")
    gmail = build("gmail", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    config = _load_config()

    messages = fetch_invoice_messages(gmail)[: args.max]
    print(f"[INFO] {len(messages)} Rechnungs-Mail(s) — Archive-Test")

    for msg in messages:
        row = message_to_invoice_row(msg)
        result = archive_message_pdfs(
            gmail,
            drive,
            msg["id"],
            msg.get("payload", {}),
            vendor=row.vendor,
            invoice_id=row.invoice_id,
            date_str=row.contract_start,
            config=config,
        )
        if result:
            print(f"  ✅ {row.vendor} → {result.get('drive_path')} | {result.get('drive_url')}")
        else:
            print(f"  –  {row.vendor} (kein PDF-Anhang)")


if __name__ == "__main__":
    main()
