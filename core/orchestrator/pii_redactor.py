"""PII Redaction Gateway — Anonymisierung sensibler Daten vor Cloud-Inference (P12/P15).

Schützt personenbezogene Daten (E-Mails, Telefonnummern, IP-Adressen, IBANs) bei der
Eskalation vom lokalen sovereign-Modus in Cloud-Modi (balanced, premium, coding).
"""

from __future__ import annotations

import re
from typing import NamedTuple

EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b")
IPV4_REGEX = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
IBAN_REGEX = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{12,30}\b")


class RedactionResult(NamedTuple):
    redacted_text: str
    mappings: dict[str, str]
    pii_count: int


def redact_pii(text: str) -> RedactionResult:
    """Maskiert sensible PII-Daten durch Platzhalter und gibt ein Re-Mapping zurück."""
    if not text:
        return RedactionResult(text, {}, 0)

    mappings: dict[str, str] = {}
    pii_count = 0

    # 1. E-Mails maskieren
    def _replace_email(match: re.Match[str]) -> str:
        nonlocal pii_count
        val = match.group(0)
        placeholder = f"[EMAIL_{len(mappings) + 1}]"
        mappings[placeholder] = val
        pii_count += 1
        return placeholder

    text = EMAIL_REGEX.sub(_replace_email, text)

    # 2. IBANs maskieren
    def _replace_iban(match: re.Match[str]) -> str:
        nonlocal pii_count
        val = match.group(0)
        placeholder = f"[IBAN_{len(mappings) + 1}]"
        mappings[placeholder] = val
        pii_count += 1
        return placeholder

    text = IBAN_REGEX.sub(_replace_iban, text)

    # 3. IP-Adressen maskieren (ausschließen von lokalen Loopback-IPs)
    def _replace_ip(match: re.Match[str]) -> str:
        nonlocal pii_count
        val = match.group(0)
        if val in {"127.0.0.1", "0.0.0.0"}:
            return val
        placeholder = f"[IP_{len(mappings) + 1}]"
        mappings[placeholder] = val
        pii_count += 1
        return placeholder

    text = IPV4_REGEX.sub(_replace_ip, text)

    # 4. Telefonnummern maskieren
    def _replace_phone(match: re.Match[str]) -> str:
        nonlocal pii_count
        val = match.group(0)
        # Kurze Zahlenfolgen wie '2026' oder '8091' ignorieren
        if len(val.replace(" ", "").replace("-", "")) < 6:
            return val
        placeholder = f"[PHONE_{len(mappings) + 1}]"
        mappings[placeholder] = val
        pii_count += 1
        return placeholder

    text = PHONE_REGEX.sub(_replace_phone, text)

    return RedactionResult(redacted_text=text, mappings=mappings, pii_count=pii_count)


def restore_pii(text: str, mappings: dict[str, str]) -> str:
    """Stellt die ursprünglichen Werte in einer geglätteten Antwort wieder her."""
    if not text or not mappings:
        return text

    restored = text
    for placeholder, original in mappings.items():
        restored = restored.replace(placeholder, original)
    return restored
