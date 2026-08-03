"""Tests für Rechnungs-Sheet-Backfill (ohne Google-API)."""

from __future__ import annotations

import os
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.google.invoice.backfill import (  # noqa: E402
    SheetRow,
    enrich_sheet_values,
    match_sheet_row,
    parse_filename_hints,
    pdf_to_invoice_row,
)
from core.google.invoice.extract import InvoiceRow  # noqa: E402


class InvoiceBackfillTests(unittest.TestCase):
    def test_parse_filename_hints(self) -> None:
        hints = parse_filename_hints("IONOS_ INV2025_2025-08-03.pdf".replace(" ", ""))
        hints = parse_filename_hints("IONOS_INV2025_2025-08-03.pdf")
        self.assertEqual(hints["vendor"], "IONOS")
        self.assertEqual(hints["invoice_id"], "INV2025")
        self.assertEqual(hints["contract_start"], "03.08.2025")

    def test_enrich_sheet_values_fills_empty_only(self) -> None:
        existing = ["IONOS", "", "", "monatlich", "01.08.2025", "", "", "", "", "INV-1", "Prüfen", ""]
        extracted = InvoiceRow(
            vendor="IONOS GmbH",
            purpose="Webhosting",
            amount="130,60",
            interval="monatlich",
            contract_start="01.08.2025",
            next_renewal="",
            cancellation_days="",
            last_cancel_date="",
            payment_method="PayPal",
            invoice_id="INV-1",
            status="Prüfen",
            source_message_id="drive:x",
            drive_url="https://drive.google.com/file/d/abc/view",
        )
        merged, changed = enrich_sheet_values(existing, extracted, force=False)
        self.assertTrue(changed)
        self.assertEqual(merged[0], "IONOS")
        self.assertEqual(merged[1], "Webhosting")
        self.assertEqual(merged[2], "130,60")
        self.assertEqual(merged[11], "https://drive.google.com/file/d/abc/view")

    def test_match_sheet_row_by_invoice_id(self) -> None:
        rows = [
            SheetRow(row_num=3, values=["Google", "", "10,00", "", "", "", "", "", "", "INV-99", "Prüfen", ""]),
        ]
        matched = match_sheet_row(
            rows,
            file_id="file123",
            drive_url="",
            invoice_id="INV-99",
            vendor="Google",
            drive_path="Rechnungen/2025/08/x.pdf",
        )
        self.assertIsNotNone(matched)
        self.assertEqual(matched.row_num, 3)

    def test_pdf_to_invoice_row_from_text(self) -> None:
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<<>>\nendobj\n"
            b"trailer\n<<>>\n"
        )
        row = pdf_to_invoice_row(
            filename="Acme_INV-42_2025-07-01.pdf",
            drive_path="Rechnungen/2025/07/Acme_INV-42_2025-07-01.pdf",
            drive_url="https://drive.google.com/file/d/xyz/view",
            file_id="xyz",
            pdf_bytes=pdf_bytes,
            ocr=False,
        )
        self.assertEqual(row.vendor, "Acme")
        self.assertEqual(row.invoice_id, "INV-42")
        self.assertEqual(row.contract_start, "01.07.2025")


if __name__ == "__main__":
    unittest.main()
