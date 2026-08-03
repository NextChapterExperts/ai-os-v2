#!/usr/bin/env python3
"""Backfill: Drive-Rechnungs-PDFs → Sheet (pypdf/OCR, gleiche Pipeline wie email-agent).

Liest alle PDFs unter dem Drive-Ordner «Rechnungen», extrahiert Felder und
reichert bestehende Google-Sheet-Zeilen an (oder legt fehlende Zeilen an).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.google.invoice.backfill import run_invoice_sheet_backfill  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rechnungs-Backfill: Drive-PDFs scannen und Google Sheet aktualisieren",
    )
    parser.add_argument("--tenant", default=os.environ.get("DEFAULT_TENANT", "nextchapter"))
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts schreiben")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bestehende Sheet-Werte überschreiben (Standard: nur leere Felder füllen)",
    )
    parser.add_argument("--no-ocr", action="store_true", help="OCR-Fallback für Scans deaktivieren")
    parser.add_argument("--limit", type=int, default=None, help="Max. Anzahl PDFs verarbeiten")
    parser.add_argument(
        "--no-add",
        action="store_true",
        help="Keine neuen Zeilen anlegen — nur bestehende Zeilen anreichern",
    )
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben")
    args = parser.parse_args()

    try:
        result = run_invoice_sheet_backfill(
            tenant_id=args.tenant,
            dry_run=args.dry_run,
            force=args.force,
            ocr=not args.no_ocr,
            limit=args.limit,
            add_missing=not args.no_add,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        mode = "DRY-RUN" if result.get("dry_run") else "LIVE"
        print(f"[INFO] Backfill ({mode}) — Tenant {result.get('tenant_id')}")
        print(f"  Sheet-Zeilen gelesen:     {result.get('sheet_rows')}")
        print(f"  PDFs gesehen/verarbeitet: {result.get('pdfs_seen')} / {result.get('pdfs_processed')}")
        print(f"  Zeilen aktualisiert:      {result.get('rows_updated')}")
        print(f"  Zeilen neu angelegt:      {result.get('rows_added')}")
        print(f"  Unverändert:              {result.get('rows_unchanged')}")
        print(f"  PDF ohne Match:           {result.get('rows_unmatched_pdf')}")
        print(f"  Fehler:                   {result.get('errors')}")
        if result.get("updates"):
            print("\n  Aktualisierte Zeilen (Auszug):")
            for item in result["updates"][:15]:
                print(f"    Zeile {item.get('row')}: {item.get('vendor')} | {item.get('invoice_id')} ← {item.get('file')}")
        if result.get("additions"):
            print("\n  Neue Zeilen (Auszug):")
            for item in result["additions"][:15]:
                print(
                    f"    + {item.get('vendor')} | {item.get('amount') or '?'} EUR | "
                    f"{item.get('invoice_id') or 'n/a'} ← {item.get('file')}"
                )

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
