"""Unit tests for PII Redaction Gateway."""

from __future__ import annotations

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from core.orchestrator.pii_redactor import redact_pii, restore_pii


def test_pii_redact_emails():
    text = "Bitte sende das Angebot an peter@nextchapter.de und info@example.com."
    res = redact_pii(text)
    assert "[EMAIL_1]" in res.redacted_text
    assert "[EMAIL_2]" in res.redacted_text
    assert "peter@nextchapter.de" not in res.redacted_text
    assert res.pii_count == 2

    restored = restore_pii(res.redacted_text, res.mappings)
    assert restored == text


def test_pii_redact_iban_and_phone():
    text = "Konto DE89370400440532013000 und Telefon +49 171 1234567 kontaktieren."
    res = redact_pii(text)
    assert "[IBAN_1]" in res.redacted_text
    assert "[PHONE_2]" in res.redacted_text or "[PHONE_1]" in res.redacted_text
    assert "DE89370400440532013000" not in res.redacted_text
    assert "+49 171 1234567" not in res.redacted_text

    restored = restore_pii(res.redacted_text, res.mappings)
    assert restored == text


def test_pii_redact_ips():
    text = "Server IP ist 192.168.178.64 und Loopback 127.0.0.1"
    res = redact_pii(text)
    assert "[IP_1]" in res.redacted_text
    assert "127.0.0.1" in res.redacted_text  # Loopback skipped
    assert "192.168.178.64" not in res.redacted_text

    restored = restore_pii(res.redacted_text, res.mappings)
    assert restored == text


def test_pii_redact_empty():
    res = redact_pii("")
    assert res.redacted_text == ""
    assert res.pii_count == 0
    assert res.mappings == {}
