"""Unit-Tests für Rechnungs-Parser (portiert aus v1 email-agent)."""

from __future__ import annotations

import os
import sys
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from core.google.invoice.enrich import combine_extraction_text
from core.google.invoice.extract import (
    extract_amount,
    extract_cancellation_days,
    extract_invoice_id,
    extract_next_renewal,
    extract_payment_method,
    extract_purpose,
    infer_vendor,
    is_invoice_candidate,
    message_to_invoice_row,
    resolve_gmail_queries,
)
from core.google.invoice.pdf_text import extract_text_from_pdf_bytes


class InvoiceParseTests(unittest.TestCase):
    def test_amount_german_thousands(self) -> None:
        self.assertEqual(extract_amount("Gesamt 10.520,00 €"), "10520,00")
        self.assertEqual(extract_amount("Betrag: 105,20 €"), "105,20")

    def test_invoice_id_rejects_stopwords(self) -> None:
        self.assertEqual(extract_invoice_id("Rechnung vom 01.07.2026", "Rechnung vom Juni"), "")
        self.assertEqual(extract_invoice_id("", "Invoice Number RALU6X65-0001"), "RALU6X65-0001")

    def test_payment_method_stops_before_betrag(self) -> None:
        body = "Zahlungsart: Credit/Debit Card Betrag: 96,00 €"
        self.assertEqual(extract_payment_method(body), "Kreditkarte")

    def test_vendor_from_sender_hint(self) -> None:
        vendor = infer_vendor(
            "Your receipt from Anthropic",
            "Anthropic, PBC <billing@anthropic.com>",
            "Invoice RALU6X65-0001",
        )
        self.assertEqual(vendor, "Anthropic")

    def test_candidate_rejects_newsletter_body(self) -> None:
        ok = is_invoice_candidate(
            "Newsletter",
            "news@example.com",
            "monatliche rechnung und payment of services in our digest",
            None,
        )
        self.assertFalse(ok)

    def test_gmail_queries_include_tax_year(self) -> None:
        queries = resolve_gmail_queries(
            {
                "gmail": {
                    "date_after": "2025/01/01",
                    "date_before": "2026/01/01",
                    "queries": ["subject:Rechnung"],
                }
            }
        )
        self.assertEqual(len(queries), 1)
        self.assertIn("after:2025/01/01", queries[0])
        self.assertIn("before:2026/01/01", queries[0])

    def test_extract_purpose_from_product_line(self) -> None:
        body = "Produkt: Google Workspace Business Standard\nBetrag: 14,40 €"
        self.assertIn("Google Workspace", extract_purpose(body, "Rechnung"))

    def test_extract_next_renewal(self) -> None:
        body = "Nächste Verlängerung: 15.08.2026"
        self.assertEqual(extract_next_renewal(body), "15.08.2026")

    def test_extract_cancellation_days(self) -> None:
        body = "Kündigungsfrist: 30 Tage vor Verlängerung"
        self.assertEqual(extract_cancellation_days(body), "30 Tage")

    def test_message_to_invoice_row_uses_pdf_text(self) -> None:
        message = {
            "id": "msg-1",
            "subject": "Rechnung IONOS",
            "sender": "billing@ionos.de",
            "date_header": "Mon, 3 Aug 2026 10:00:00 +0200",
            "body": "Sehr geehrter Kunde, anbei Ihre Rechnung.",
        }
        pdf_text = "Rechnungsnummer INV-2026-99\nBetrag: 130,60 €\nProdukt: Webhosting Premium"
        row = message_to_invoice_row(message, pdf_text=pdf_text)
        self.assertEqual(row.invoice_id, "INV-2026-99")
        self.assertEqual(row.amount, "130,60")
        self.assertIn("Webhosting", row.purpose)

    def test_combine_extraction_text(self) -> None:
        combined = combine_extraction_text("Mail-Body", "--- PDF ---\n130,60 €")
        self.assertIn("Mail-Body", combined)
        self.assertIn("130,60", combined)

    def test_pdf_text_empty_for_invalid_bytes(self) -> None:
        self.assertEqual(extract_text_from_pdf_bytes(b"", ocr=False), "")


if __name__ == "__main__":
    unittest.main()
