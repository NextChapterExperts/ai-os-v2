#!/usr/bin/env python3
"""2025-Rechnungs-PDFs aus Gmail nach Steuer2025/Rechnungen/<Lieferant>/ exportieren."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from core.google import auth
from core.google.invoice.config import load_invoice_config
from core.google.invoice.extract import (
    _parse_message_year,
    expand_invoice_bundle,
    fetch_invoice_messages,
    is_invoice_bundle,
    message_to_invoice_row,
    resolve_gmail_queries,
)
from core.google.invoice.mime import collect_pdf_attachments, pdfs_from_parsed_message
from googleapiclient.discovery import build

DEFAULT_DEST = Path("/home/peter/peters-brain/Projekte/Steuer2025/rechnungen")
TAX_YEAR = 2025


def _safe_vendor_dir(name: str) -> str:
    cleaned = re.sub(r"[^\w\s\-&.+]", "", name.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:60] or "Unbekannt"


def _invoice_year(row, msg: dict) -> int | None:
    subject = msg.get("subject", "")
    body = msg.get("body", "")

    vom_match = re.search(r"vom\s+\d{2}\.\d{2}\.(20\d{2})", subject, re.IGNORECASE)
    if vom_match:
        return int(vom_match.group(1))

    if row.invoice_id:
        id_match = re.search(r"(20\d{2})(\d{2})(\d{2})", row.invoice_id)
        if id_match:
            return int(id_match.group(1))

    for src in (subject, body[:500]):
        year_match = re.search(r"\b(20\d{2})\b", src)
        if year_match:
            year = int(year_match.group(1))
            if 2000 <= year <= 2100:
                return year

    if row.contract_start:
        match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", row.contract_start)
        if match:
            return int(match.group(3))

    return _parse_message_year(
        msg.get("date_header", ""),
        subject,
        body,
    )


def _is_tax_year(year: int | None, tax_year: int) -> bool:
    return year == tax_year


VENDOR_SUBJECT_HINTS: tuple[tuple[str, str], ...] = (
    ("deepl", "DeepL"),
    ("ionos", "IONOS"),
    ("telekom", "Telekom"),
    ("tuxedo", "TUXEDO"),
    ("homodea", "homodea"),
    ("blau", "Blau"),
    ("paypal", "PayPal"),
    ("logpay", "LogPay"),
    ("xmind", "Xmind"),
    ("schokokeks", "schokokeks.org"),
    ("oelfreund", "oelfreund.de"),
    ("portknox", "Portknox"),
    ("projektwerkstatt", "Projektwerkstatt"),
    ("vrn ticket", "VRN"),
    ("vertragszusammenfassung", "Versicherung"),
    ("erinnerung an unsere rechnung", "Diverse"),
    ("sipgate", "sipgate"),
    ("hugendubel", "Hugendubel"),
    ("github", "GitHub"),
    ("google play", "Google Play"),
)


def _refine_vendor(vendor: str, subject: str, sender: str) -> str:
    combined = f"{subject}\n{sender}".lower()
    for needle, label in VENDOR_SUBJECT_HINTS:
        if needle in combined:
            return label
    cleaned = _safe_vendor_dir(vendor)
    if cleaned.lower().startswith("e und services") or cleaned.lower().startswith("menge preis"):
        for needle, label in VENDOR_SUBJECT_HINTS:
            if needle in subject.lower():
                return label
    return cleaned


def _target_filename(
    vendor: str,
    invoice_id: str,
    date_str: str,
    source_name: str,
    index: int,
) -> str:
    stem_parts = [_safe_vendor_dir(vendor).replace(" ", "_")]
    if invoice_id:
        stem_parts.append(re.sub(r"[^\w\-]+", "_", invoice_id)[:30])
    if date_str:
        stem_parts.append(re.sub(r"[^\d]", "", date_str)[:8])
    elif re.search(r"20\d{2}", source_name):
        stem_parts.append(re.search(r"20\d{2}[-_]?\d{2}[-_]?\d{2}", source_name).group(0))  # type: ignore[union-attr]
    stem = "_".join(p for p in stem_parts if p) or "Rechnung"
    if index:
        stem += f"_{index + 1}"
    return stem


def _write_invoice_files(
    vendor: str,
    invoice_id: str,
    date_str: str,
    pdfs: list[tuple[str, bytes]],
    eml_bytes: bytes | None,
    dest: Path,
    msg_id: str,
    *,
    dry_run: bool,
) -> list[str]:
    vendor_dir = dest / _safe_vendor_dir(vendor)
    written: list[str] = []

    if pdfs:
        if not dry_run:
            vendor_dir.mkdir(parents=True, exist_ok=True)
        for idx, (source_name, data) in enumerate(pdfs):
            fname = _target_filename(vendor, invoice_id, date_str, source_name, idx if len(pdfs) > 1 else 0)
            if not fname.lower().endswith(".pdf"):
                fname += ".pdf"
            target = vendor_dir / fname
            if target.exists() and not dry_run:
                target = vendor_dir / f"{target.stem}_{msg_id.replace('#', '_')[-12:]}.pdf"
            written.append(str(target))
            if not dry_run:
                target.write_bytes(data)
        return written

    if eml_bytes:
        if not dry_run:
            vendor_dir.mkdir(parents=True, exist_ok=True)
        fname = _target_filename(vendor, invoice_id, date_str, "rechnung.eml", 0) + ".eml"
        target = vendor_dir / fname
        if target.exists() and not dry_run:
            target = vendor_dir / f"{target.stem}_{msg_id.replace('#', '_')[-12:]}.eml"
        written.append(str(target))
        if not dry_run:
            target.write_bytes(eml_bytes)
    return written


def _collect_messages(gmail, *, include_bundle: bool = True) -> list[dict]:
    config = load_invoice_config()
    gmail_cfg = dict(config.get("gmail") or {})
    gmail_cfg["date_after"] = f"{TAX_YEAR}/01/01"
    gmail_cfg["date_before"] = f"{TAX_YEAR + 1}/01/01"
    config = {**config, "gmail": gmail_cfg}

    messages = fetch_invoice_messages(
        gmail,
        full_inbox=gmail_cfg.get("full_inbox_scan", False),
        processed_label=gmail_cfg.get("processed_label", "R-Verarbeitet"),
        skip_processed=False,
        reprocess_if_pdfs_remain=False,
        gmail_queries=resolve_gmail_queries(config),
    )

    if not include_bundle:
        return messages

    extra: list[dict] = []
    for mid in ("19eb677cfad5ccd7",):
        try:
            msg = gmail.users().messages().get(userId="me", id=mid, format="full").execute()
        except Exception:
            continue
        headers = {
            h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])
        }
        subject = headers.get("subject", "")
        if not is_invoice_bundle(subject, msg["payload"]):
            continue
        expanded = expand_invoice_bundle(
            gmail,
            mid,
            msg["payload"],
            parent_date_header=headers.get("date", ""),
            config=config,
        )
        if expanded:
            extra.extend(expanded)

    by_id = {m["id"]: m for m in messages}
    for item in extra:
        by_id[item["id"]] = item
    return list(by_id.values())


def export_rechnungen(
    dest: Path,
    *,
    tax_year: int = TAX_YEAR,
    dry_run: bool = False,
) -> dict:
    creds = auth.load_credentials(
        ["https://www.googleapis.com/auth/gmail.readonly"],
        "token.json",
    )
    gmail = build("gmail", "v1", credentials=creds)
    messages = _collect_messages(gmail)

    stats = {
        "messages": len(messages),
        "exported": 0,
        "exported_pdf": 0,
        "exported_eml": 0,
        "skipped_empty": 0,
        "skipped_year": 0,
        "vendors": set(),
        "files": [],
    }

    dest.mkdir(parents=True, exist_ok=True)

    for msg in messages:
        row = message_to_invoice_row(msg)
        vendor = _refine_vendor(row.vendor, msg.get("subject", ""), msg.get("sender", ""))
        year = _invoice_year(row, msg)
        if not _is_tax_year(year, tax_year):
            stats["skipped_year"] += 1
            continue

        if msg.get("parsed_eml") is not None:
            pdfs = pdfs_from_parsed_message(msg["parsed_eml"])
        else:
            pdfs = collect_pdf_attachments(
                gmail, msg["id"].split("#")[0], msg.get("payload", {})
            )

        eml_bytes = msg.get("eml_bytes")
        subject_lower = msg.get("subject", "").lower()
        if not pdfs and not eml_bytes:
            stats["skipped_empty"] += 1
            continue
        if not pdfs and "bestellbestätigung" in subject_lower and "rechnung" not in subject_lower:
            stats["skipped_empty"] += 1
            continue

        written = _write_invoice_files(
            vendor,
            row.invoice_id,
            row.contract_start,
            pdfs,
            eml_bytes if not pdfs else None,
            dest,
            msg["id"],
            dry_run=dry_run,
        )
        if not written:
            stats["skipped_empty"] += 1
            continue

        stats["vendors"].add(_safe_vendor_dir(vendor))
        stats["files"].extend(written)
        stats["exported"] += len(written)
        if pdfs:
            stats["exported_pdf"] += len(written)
        else:
            stats["exported_eml"] += len(written)

    stats["vendors"] = sorted(stats["vendors"])  # type: ignore[assignment]
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Steuer2025-Rechnungen nach Lieferant exportieren")
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help=f"Zielverzeichnis (Default: {DEFAULT_DEST})",
    )
    parser.add_argument("--year", type=int, default=TAX_YEAR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json-lines", action="store_true")
    args = parser.parse_args()

    stats = export_rechnungen(args.dest, tax_year=args.year, dry_run=args.dry_run)
    if args.json_lines:
        import json

        payload = {
            "type": "done",
            **stats,
            "dest": str(args.dest),
            "dry_run": args.dry_run,
            "year": args.year,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return

    print(f"[INFO] Nachrichten: {stats['messages']}")
    print(f"[INFO] Exportiert: {stats['exported']} Datei(en) ({stats['exported_pdf']} PDF, {stats['exported_eml']} EML)")
    print(f"[INFO] Übersprungen (Jahr): {stats['skipped_year']}")
    print(f"[INFO] Übersprungen (leer): {stats['skipped_empty']}")
    print(f"[INFO] Lieferanten ({len(stats['vendors'])}):")
    for vendor in stats["vendors"]:
        print(f"  - {vendor}")
    print(f"[INFO] Ziel: {args.dest}")


if __name__ == "__main__":
    main()
