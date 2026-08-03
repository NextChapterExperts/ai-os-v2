"""Extract invoice data from Gmail and write rows to the business spreadsheet."""

import base64
import html
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

from core.google import auth
from core.google.gmail_client import is_message_processed, resolve_label_id
from core.google.invoice.config import load_invoice_config
from core.google.invoice.mime import (
    count_bundle_eml_attachments,
    extract_all_text,
    has_invoice_attachment,
    list_bundle_eml_attachments,
    pdfs_from_parsed_message,
    texts_from_parsed_message,
)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

SPREADSHEET_ID = "1pE4zOZlf2vZsbfAjKTEOhC8BGAE6gg7C4ck-ULQIZqQ"
SHEET_NAME = "Übersicht"
DATA_START_ROW = 3

GMAIL_QUERIES = [
    (
        "subject:(Rechnung OR Invoice OR receipt OR Beleg OR Quittung OR "
        "Zahlung OR payment OR billing OR Abrechnung OR Bestellbestätigung) "
        "OR Bestellnummer OR Rechnungsnummer"
    ),
    (
        "from:(payments-noreply@google.com OR abo@info.service-hmg.com OR "
        "billing OR invoice OR stripe.com OR paypal.com OR anthropic.com OR "
        "paddle.com OR ionos.de OR vodafone.de)"
    ),
    "has:attachment filename:pdf",
]


def _load_invoice_config() -> dict:
    return load_invoice_config()


def resolve_gmail_queries(config: dict | None = None) -> list[str]:
    cfg = config if config is not None else _load_invoice_config()
    gmail_cfg = cfg.get("gmail") or {}
    queries = gmail_cfg.get("queries") or GMAIL_QUERIES
    prefix_parts: list[str] = []
    if gmail_cfg.get("date_after"):
        prefix_parts.append(f"after:{gmail_cfg['date_after']}")
    if gmail_cfg.get("date_before"):
        prefix_parts.append(f"before:{gmail_cfg['date_before']}")
    if not prefix_parts:
        return list(queries)
    prefix = " ".join(prefix_parts)
    return [f"{prefix} ({query})" if " OR " in query else f"{prefix} {query}" for query in queries]

INVOICE_BODY_PHRASES = (
    "rechnungsnummer",
    "invoice number",
    "invoice #",
    "rechnung nr",
    "zahlung in höhe von",
    "payment of",
    "amount paid",
    "wir haben ihre zahlung",
    "payment received",
    "zahlung erhalten",
    "bestellbestätigung",
    "order confirmation",
    "bestellnummer",
    "order number",
    "your receipt",
    "payment receipt",
    "monatliche rechnung",
    "monthly invoice",
    "billing statement",
    "automatisch belastet",
    "automatically charged",
    "first billing date",
)

NOISE_SENDER_TERMS = (
    "linkedin",
    "community-notification",
    "newsletter@email.wiwo.de",
    "weekender@redaktion.wiwo.de",
    "coach@redaktion.wiwo.de",
    "newsletters-noreply@linkedin.com",
    "news@mail.dazn.com",
    "noreply-marketing",
    "@news.",
    "hej.news.",
    "mobilization.",
    "@hello@",
    "mozillafoundation.org",
    "ikea@hej.news",
    "miele@news.",
)

NOISE_SUBJECT_TERMS = (
    "digest",
    "newsletter",
    "daily digest",
    "verification",
    "bestätigen",
    "confirm your",
    "login",
    "sign in",
    "passwort",
    "password",
    "vorbeikommen",
    "wieder online",
    "mozfest",
    "mozilla festival",
    "reservierung",
    "reservation",
    "steuerausgleich",
    "außergewöhnliche belastungen",
    "muster für dich",
)

BUNDLE_SUBJECT_MARKERS = (
    "rechnungen aus bezahldienste",
    "bezahldienste",
)
MIN_BUNDLE_EML_COUNT = 5

NESTED_INVOICE_SUBJECT_TERMS = (
    "rechnung",
    "invoice",
    "beleg",
    "zahlung",
    "receipt",
    "billing",
    "payment",
    "bestellbestätigung",
    "bestellung",
    "ionos",
    "paypal",
    "github",
    "paddle",
    "stripe",
    "homodea",
    "telekom",
    "vodafone",
    "blau",
    "deepl",
    "tuxedo",
    "sipgate",
    "hugendubel",
    "portknox",
)

INVOICE_TERMS = (
    "rechnung",
    "invoice",
    "payment",
    "zahlung",
    "receipt",
    "beleg",
    "billing",
    "abrechnung",
    "rechnungsnummer",
)

INVOICE_ID_STOPWORDS = frozenset({
    "und", "oder", "vom", "von", "vor", "nicht", "ben", "zu", "f", "en", "an",
    "klicke", "wie", "findest", "aktivieren", "erteilt", "online", "wird",
    "handelt", "sollten", "domains", "ssl", "email", "office", "websites",
    "the", "your", "for", "from", "with", "this", "that", "invoice", "rechnung",
    "nummer", "number", "bestell", "order", "receipt", "payment", "zahlung",
})

SENDER_VENDOR_HINTS: tuple[tuple[str, str], ...] = (
    ("payments-noreply@google.com", "Google Payments"),
    ("workspace-noreply@google.com", "Google Workspace"),
    ("googleplay-noreply@google.com", "Google Play"),
    ("stripe.com", "Stripe"),
    ("paypal.com", "PayPal"),
    ("anthropic.com", "Anthropic"),
    ("paddle.com", "Paddle"),
    ("vodafone.de", "Vodafone"),
    ("1und1.de", "1&1"),
    ("ionos.de", "IONOS"),
    ("buhl.de", "Buhl Data Service"),
    ("handelsblatt.com", "Handelsblatt"),
    ("finanzen.net", "finanzen.net ZERO"),
    ("raisin.com", "Raisin Bank"),
    ("homodea", "homodea"),
    ("bauhaus.info", "BAUHAUS"),
    ("ikea.de", "IKEA"),
    ("miele.de", "Miele"),
    ("cursor.com", "Cursor"),
    ("cursor.sh", "Cursor"),
)

PERSONAL_EMAIL_DOMAINS = frozenset({
    "gmail.com",
    "googlemail.com",
    "gmx.net",
    "gmx.de",
    "web.de",
    "t-online.de",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "icloud.com",
})

DOMAIN_VENDOR_LABELS: dict[str, str] = {
    "bauhaus.info": "BAUHAUS",
    "ikea.de": "IKEA",
    "miele.de": "Miele",
    "ionos.de": "IONOS",
    "vodafone.de": "Vodafone",
    "handelsblatt.com": "Handelsblatt",
    "finanzen.net": "finanzen.net ZERO",
    "raisin.com": "Raisin Bank",
    "anthropic.com": "Anthropic",
    "paddle.com": "Paddle",
    "stripe.com": "Stripe",
    "paypal.com": "PayPal",
    "homodea.com": "homodea",
    "homodea.de": "homodea",
    "cursor.com": "Cursor",
    "cursor.sh": "Cursor",
}

VENDOR_PROSE_STARTERS = (
    "das ", "die ", "der ", "wird ", "werden ", "an uns ", "entwicklung ",
    "online ", "hallo", "wenn sie ", "wir sind ", "wir haben ", "vielen dank",
)

VENDOR_GARBAGE_MARKERS = (
    " handelt es sich",
    " sollten nicht",
    " auf den markt",
    " jeden tag",
    " domains &",
    " websites &",
    " hosting server",
    " digitale vermögensverwaltung",
    " erfolgt in k",
)


def _parse_eur_amount(raw: str) -> float | None:
    s = raw.strip().replace(" ", "").replace("€", "")
    if not s or not re.search(r"\d", s):
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d{1,2}", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d+,\d{1,2}", s):
        s = s.replace(",", ".")
    elif re.fullmatch(r"\d+\.\d{1,2}", s):
        pass
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    else:
        s = s.replace(".", "").replace(",", ".")
    try:
        value = float(s)
    except ValueError:
        return None
    if value <= 0 or value > 1_000_000:
        return None
    return value


def _format_eur_amount(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _valid_invoice_id(value: str) -> bool:
    v = value.strip()
    if len(v) < 4 or len(v) > 40:
        return False
    lower = v.lower()
    if lower in INVOICE_ID_STOPWORDS:
        return False
    if re.fullmatch(r"[a-zäöüß]+", lower):
        return False
    if re.search(r"\d", v):
        return True
    return bool(re.fullmatch(r"[A-Z0-9]{2,}-[A-Z0-9-]+", v, re.IGNORECASE))


def _vendor_from_email_domain(sender: str) -> str:
    match = re.search(r"@([\w.-]+\.\w+)", sender.lower())
    if not match:
        return ""
    domain = match.group(1)
    if domain in PERSONAL_EMAIL_DOMAINS:
        return ""
    if domain in DOMAIN_VENDOR_LABELS:
        return DOMAIN_VENDOR_LABELS[domain]
    for suffix, label in DOMAIN_VENDOR_LABELS.items():
        if domain.endswith("." + suffix) or domain == suffix:
            return label
    base = domain.split(".")[-2] if domain.count(".") >= 1 else domain.split(".")[0]
    if len(base) >= 3 and base not in {"mail", "news", "info", "service", "noreply"}:
        return base.replace("-", " ").title()
    return ""


def _looks_like_prose_vendor(text: str) -> bool:
    lower = text.lower().strip()
    if any(lower.startswith(starter) for starter in VENDOR_PROSE_STARTERS):
        return True
    if " bis hin zu " in lower or lower.endswith(" und"):
        return True
    return False


def _clean_vendor(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name).strip()
    if len(cleaned) < 2 or len(cleaned) > 60:
        return ""
    lower = cleaned.lower()
    if any(marker in lower for marker in VENDOR_GARBAGE_MARKERS):
        return ""
    if _looks_like_prose_vendor(cleaned):
        return ""
    if cleaned.count(" ") > 8:
        return ""
    return cleaned


def _sender_vendor_hint(sender: str) -> str:
    sender_lower = sender.lower()
    for needle, label in SENDER_VENDOR_HINTS:
        if needle in sender_lower:
            return label
    return ""


@dataclass
class InvoiceRow:
    vendor: str
    purpose: str
    amount: str
    interval: str
    contract_start: str
    next_renewal: str
    cancellation_days: str
    last_cancel_date: str
    payment_method: str
    invoice_id: str
    status: str
    source_message_id: str
    drive_url: str = ""
    drive_path: str = ""

    def to_sheet_row(self) -> list[str]:
        return [
            self.vendor,
            self.purpose,
            self.amount,
            self.interval,
            self.contract_start,
            self.next_renewal,
            self.cancellation_days,
            self.last_cancel_date,
            self.payment_method,
            self.invoice_id,
            self.status,
            self.drive_url or self.drive_path,
        ]


def load_credentials() -> Credentials:
    return auth.load_credentials(SCOPES, "token.json")


def get_message_body(payload: dict) -> str:
    texts: list[tuple[str, str]] = []

    def walk(part: dict) -> None:
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data:
            raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            if mime == "text/plain":
                texts.append(("plain", raw))
            elif mime == "text/html":
                texts.append(("html", raw))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    plain = next((text for kind, text in texts if kind == "plain"), None)
    if plain:
        return plain
    if texts:
        html_text = next((text for kind, text in texts if kind == "html"), texts[0][1])
        cleaned = re.sub(r"<[^>]+>", " ", html.unescape(html_text))
        return re.sub(r"\s+", " ", cleaned)
    return ""


def parse_sender_name(sender: str) -> str:
    match = re.match(r"^([^<]+)", sender.strip())
    if match:
        name = match.group(1).strip().strip('"')
        if name:
            return name
    email_match = re.search(r"@([\w.-]+)", sender)
    if email_match:
        return email_match.group(1).split(".")[0].title()
    return sender[:80]


def parse_email_date(date_header: str) -> str:
    if not date_header:
        return ""
    body_date = re.search(r"(?:Datum|Date)\s*[:\s]*(\d{2}\.\d{2}\.\d{4})", date_header)
    if body_date:
        return body_date.group(1)
    try:
        dt = parsedate_to_datetime(date_header)
        if dt.tzinfo:
            dt = dt.astimezone()
        return dt.strftime("%d.%m.%Y")
    except (TypeError, ValueError, OverflowError):
        return ""


def extract_contract_date(body: str, date_header: str) -> str:
    patterns = [
        r"Datum\s*[:\s]*(\d{2}\.\d{2}\.\d{4})",
        r"First billing date\s*[:\s]*([A-Za-z]+ \d{1,2}, \d{4})",
        r"First billing date[\s\S]{0,40}?([A-Za-z]+ \d{1,2}, \d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if not match:
            continue
        value = match.group(1)
        if re.match(r"\d{2}\.\d{2}\.\d{4}", value):
            return value
        try:
            dt = datetime.strptime(value, "%B %d, %Y")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            continue
    return parse_email_date(date_header)


_AMOUNT_LABEL = (
    r"(?<![a-zäöüß])(?:Zahlung in Höhe von|Betrag|Amount|Total|Summe|Gesamt|Preis)\b"
)


def extract_amount(text: str, *, strict: bool = False) -> str:
    labeled_patterns = [
        rf"{_AMOUNT_LABEL}\s*[:\s]*([\d.,]+)\s*€",
        rf"{_AMOUNT_LABEL}\s*[:\s]*€?\s*([\d.,]+)",
        r"([\d.,]+)\s*€\s*(?:pro|/)\s*(?:Monat|Jahr|month|year)",
    ]
    for pattern in labeled_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            prefix = text[max(0, match.start() - 30): match.start()].lower()
            if any(
                bad in prefix
                for bad in ("normalpreis", "statt", "uvp", "ab ", "themen", "insgesamt")
            ):
                continue
            number = _parse_eur_amount(match.group(1))
            if number is not None:
                return _format_eur_amount(number)

    if strict:
        return ""

    loose_patterns = [
        r"(?<![\d.])([\d]{1,3}(?:\.\d{3})*,\d{2})\s*€",
        r"(?<![\d.])([\d]+,\d{2})\s*€",
    ]
    invoice_context = (
        "betrag", "total", "summe", "zahlung", "invoice",
        "rechnung", "payment", "amount paid", "bezahlt", "paid",
    )
    for pattern in loose_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = text[max(0, match.start() - 50): match.end() + 20].lower()
            if "insgesamt" in context or "normalpreis" in context:
                continue
            if any(term in context for term in invoice_context):
                number = _parse_eur_amount(match.group(1))
                if number is not None:
                    return _format_eur_amount(number)
    return ""


def extract_invoice_id(text: str, subject: str) -> str:
    patterns = [
        r"Rechnungsnummer\s*[:\s#]*([A-Z0-9][A-Z0-9/-]{2,})",
        r"Bestellnummer\s*[:\s#]*(\d{4,})",
        r"Invoice\s*(?:Number|No\.?|#)\s*[:\s#]*([A-Z0-9][A-Z0-9/-]{2,})",
        r"Rechnung\s*(?:Nr\.?|nummer|#)\s*[:\s#]*([A-Z0-9][A-Z0-9/-]{2,})",
        r"Order\s*(?:Number|No\.?|#)\s*[:\s#]*([A-Z0-9][A-Z0-9/-]{2,})",
        r"Receipt\s*(?:#|Number|No\.?)\s*[:\s#]*([A-Z0-9][A-Z0-9/-]{2,})",
        r"Rechnungs-Nr\.?\s*[:\s#]*([A-Z0-9][A-Z0-9/-]{2,})",
    ]
    combined = f"{subject}\n{text}"
    for pattern in patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match and _valid_invoice_id(match.group(1)):
            return match.group(1).strip()
    return ""


def extract_payment_method(text: str) -> str:
    cleaned = re.sub(r"https?://\S+", " ", text)
    lowered = cleaned.lower()
    if "automatisch belastet" in lowered or "automatically charged" in lowered:
        return "Automatische Belastung"
    if "kreditkarte" in lowered or "credit card" in lowered or "credit/debit card" in lowered:
        return "Kreditkarte"
    if re.search(r"zahlungsart\s*[:\s]*paypal", lowered):
        return "PayPal"
    if "paypal" in lowered and "zahlungsart" in lowered:
        return "PayPal"
    if re.search(r"zahlungsart\s*[:\s]*sepa", lowered) or "sepa-lastschrift" in lowered:
        return "SEPA-Lastschrift"
    if "lastschrift" in lowered and "zahlungsart" in lowered:
        return "SEPA-Lastschrift"
    if "überweisung" in lowered or "bank transfer" in lowered:
        return "Überweisung"
    payment_match = re.search(
        r"Zahlungsart\s*[:\s]*([A-Za-z0-9 /-]+?)(?:\s+Betrag|\s+€|\s*$)",
        cleaned,
        re.IGNORECASE,
    )
    if payment_match:
        return payment_match.group(1).strip()[:40]
    return ""


def extract_purpose(text: str, subject: str) -> str:
    patterns = [
        r"Produkt\s*[:\s]*([^\n\r]{2,80})",
        r"Leistung\s*[:\s]*([^\n\r]{2,80})",
        r"Beschreibung\s*[:\s]*([^\n\r]{2,80})",
        r"Description\s*[:\s]*([^\n\r]{2,80})",
        r"Rechnung für\s+([^\n\r]{2,80})",
        r"Invoice for\s+([^\n\r]{2,80})",
        r"Your receipt from\s+([^\n\r]{2,50})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            purpose = _clean_vendor(match.group(1).strip())
            if purpose and len(purpose) > 2:
                return purpose[:80]

    subject_clean = re.sub(r"^(re:\s*)+", "", subject, flags=re.IGNORECASE).strip()
    for prefix in ("Rechnung ", "Invoice ", "Receipt from ", "Your receipt from "):
        if subject_clean.lower().startswith(prefix.lower()):
            rest = subject_clean[len(prefix) :].strip()
            if rest:
                cleaned = _clean_vendor(rest)
                if cleaned:
                    return cleaned[:80]
    return ""


def extract_next_renewal(text: str) -> str:
    patterns = [
        r"(?:Nächste Verlängerung|Next renewal|Verlängerung am|Renewal date)\s*[:\s]*(\d{2}\.\d{2}\.\d{4})",
        r"(?:Nächste Verlängerung|Next renewal)\s*[:\s]*([A-Za-z]+ \d{1,2}, \d{4})",
        r"(?:Verlängert sich am|Renews on)\s*[:\s]*(\d{2}\.\d{2}\.\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        value = match.group(1)
        if re.match(r"\d{2}\.\d{2}\.\d{4}", value):
            return value
        try:
            dt = datetime.strptime(value, "%B %d, %Y")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            continue
    return ""


def extract_cancellation_days(text: str) -> str:
    patterns = [
        r"(?:Kündigungsfrist|Notice period|Cancellation notice)\s*[:\s]*(\d+)\s*(?:Tage|Tag|days?)",
        r"(?:Kündigungsfrist|Notice period)\s*[:\s]*(\d+)\s*(?:Monate|months?)",
        r"(\d+)\s*(?:Tage|Tag)\s*(?:Kündigungsfrist|notice)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            unit = "Monate" if "monat" in pattern.lower() else "Tage"
            return f"{match.group(1)} {unit}"
    return ""


def infer_interval(text: str, subject: str) -> str:
    combined = f"{subject}\n{text}".lower()
    if any(term in combined for term in ("monatlich", "monthly", "monatsrechnung")):
        return "monatlich"
    if any(term in combined for term in ("quartals", "quarterly")):
        return "quartalsweise"
    if any(term in combined for term in ("jährlich", "yearly", "annual")):
        return "jährlich"
    return "einmalig"


def infer_vendor(subject: str, sender: str, body: str) -> str:
    hinted = _sender_vendor_hint(sender)
    if hinted:
        if "google workspace" in f"{subject}\n{body}".lower():
            domain_match = re.search(r"Domain\s+([\w.-]+)", body, re.IGNORECASE)
            if domain_match:
                return f"Google Workspace ({domain_match.group(1)})"
        return hinted

    receipt_match = re.search(
        r"(?:Your receipt from|Receipt from|Rechnung von)\s+([^\n\r<]{2,50})",
        f"{subject}\n{body}",
        re.IGNORECASE,
    )
    if receipt_match:
        vendor = _clean_vendor(receipt_match.group(1).strip())
        if vendor:
            return vendor

    sender_name = parse_sender_name(sender)
    combined = f"{subject}\n{body}".lower()

    if "google workspace" in combined or "ai expanded access" in combined:
        domain_match = re.search(r"Domain\s+([\w.-]+)", body, re.IGNORECASE)
        domain = domain_match.group(1) if domain_match else ""
        if "ai expanded access" in combined:
            label = "Google AI Expanded Access"
        else:
            label = "Google Workspace"
        if domain:
            return f"{label} ({domain})"
        return label

    product_match = re.search(r"Produkt\s*[:\s]*([^\n\r]{2,60})", body, re.IGNORECASE)
    if product_match:
        product = _clean_vendor(product_match.group(1))
        if product:
            return product

    domain_vendor = _vendor_from_email_domain(sender)
    if domain_vendor:
        return domain_vendor

    if sender_name.lower() not in {"no-reply", "noreply", "mail", "no-reply@bauhaus.info"}:
        cleaned = _clean_vendor(sender_name)
        if cleaned:
            return cleaned

    subject_clean = re.sub(r"^(re:\s*)+", "", subject, flags=re.IGNORECASE).strip()
    if subject_clean:
        cleaned = _clean_vendor(subject_clean)
        if cleaned:
            return cleaned
    return _clean_vendor(sender_name) or sender_name[:60]


def _parse_message_year(date_header: str, subject: str, body: str) -> int | None:
    for src in (date_header, subject, body[:800]):
        for match in re.finditer(r"(20\d{2})", src):
            year = int(match.group(1))
            if 2000 <= year <= 2100:
                return year
    if date_header:
        try:
            dt = parsedate_to_datetime(date_header)
            return dt.year
        except (TypeError, ValueError, OverflowError):
            pass
    return None


def _in_tax_date_window(date_header: str, subject: str, body: str, config: dict) -> bool:
    gmail_cfg = config.get("gmail") or {}
    after = gmail_cfg.get("date_after")
    before = gmail_cfg.get("date_before")
    if not after and not before:
        return True

    year = _parse_message_year(date_header, subject, body)
    if year is None:
        return True

    if after:
        try:
            min_year = int(str(after).split("/")[0])
            if year < min_year:
                return False
        except ValueError:
            pass
    if before:
        try:
            max_year = int(str(before).split("/")[0])
            if year >= max_year:
                return False
        except ValueError:
            pass
    return True


def is_invoice_bundle(subject: str, payload: dict) -> bool:
    subject_lower = subject.lower()
    if any(marker in subject_lower for marker in BUNDLE_SUBJECT_MARKERS):
        return True
    return count_bundle_eml_attachments(payload) >= MIN_BUNDLE_EML_COUNT


def is_nested_eml_invoice_candidate(subject: str, sender: str, body: str, parsed) -> bool:
    if is_invoice_candidate(subject, sender, body, None):
        return True
    pdfs = pdfs_from_parsed_message(parsed)
    if not pdfs:
        return False
    combined = f"{subject}\n{sender}\n{body}".lower()
    return any(term in combined for term in NESTED_INVOICE_SUBJECT_TERMS)


def should_include_nested_eml(
    subject: str,
    sender: str,
    body: str,
    parsed,
    config: dict,
) -> bool:
    if not _in_tax_date_window(
        str(parsed.get("Date") or ""),
        subject,
        body,
        config,
    ):
        return False
    if is_nested_eml_invoice_candidate(subject, sender, body, parsed):
        return True

    gmail_cfg = config.get("gmail") or {}
    after = gmail_cfg.get("date_after")
    min_year = int(str(after).split("/")[0]) if after else None
    year = _parse_message_year(str(parsed.get("Date") or ""), subject, body)
    if min_year and year and year < min_year:
        return False

    subject_lower = subject.lower()
    if any(term in subject_lower for term in NESTED_INVOICE_SUBJECT_TERMS):
        return True
    if extract_invoice_id(body, subject) or extract_amount(body):
        return True
    return False


def expand_invoice_bundle(
    gmail_service,
    message_id: str,
    payload: dict,
    *,
    parent_date_header: str = "",
    config: dict | None = None,
    pdf_ocr: bool = True,
) -> list[dict]:
    """Sammelmail in einzelne Rechnungs-Nachrichten aufsplitten."""
    from core.google.invoice.mime import pdfs_from_parsed_message
    from core.google.invoice.pdf_text import texts_from_pdf_attachments

    cfg = config if config is not None else _load_invoice_config()
    nested_items = list_bundle_eml_attachments(gmail_service, message_id, payload)
    expanded: list[dict] = []

    for item in nested_items:
        parsed = item["parsed"]
        subject = str(parsed.get("Subject") or item["filename"]).strip()
        sender = str(parsed.get("From") or "").strip()
        date_header = str(parsed.get("Date") or parent_date_header).strip()
        body = texts_from_parsed_message(parsed)
        pdf_text = texts_from_pdf_attachments(pdfs_from_parsed_message(parsed), ocr=pdf_ocr)

        if not should_include_nested_eml(subject, sender, body, parsed, cfg):
            continue

        expanded.append(
            {
                "id": f"{message_id}#eml{item['index']}",
                "parent_id": message_id,
                "subject": subject,
                "sender": sender,
                "date_header": date_header,
                "body": body,
                "pdf_text": pdf_text,
                "parsed_eml": parsed,
                "eml_bytes": item.get("raw_bytes"),
                "bundle_filename": item["filename"],
                "bundle_index": item["index"],
            }
        )

    return expanded


def is_invoice_candidate(subject: str, sender: str, body: str, payload: dict | None = None) -> bool:
    subject_lower = subject.lower()
    sender_lower = sender.lower()
    body_lower = body.lower()
    combined = f"{subject_lower}\n{sender_lower}\n{body_lower}"

    if any(term in subject_lower for term in NOISE_SUBJECT_TERMS):
        return False
    if any(term in sender_lower for term in NOISE_SENDER_TERMS):
        return False

    has_invoice_id = bool(extract_invoice_id(body, subject))
    has_amount = bool(extract_amount(body, strict=True))
    has_loose_amount = bool(extract_amount(body, strict=False))
    has_invoice_subject = any(term in subject_lower for term in INVOICE_TERMS)
    has_invoice_body = any(phrase in combined for phrase in INVOICE_BODY_PHRASES)
    has_payment_confirmation = any(
        phrase in combined
        for phrase in (
            "zahlung in höhe von",
            "payment received",
            "zahlung erhalten",
            "wir haben ihre zahlung",
            "bestellbestätigung",
        )
    )
    known_billing_sender = bool(_sender_vendor_hint(sender)) or any(
        domain in sender_lower
        for domain in (
            "payments-noreply@google.com",
            "workspace-noreply@google.com",
            "abo@info.service-hmg.com",
            "stripe.com",
            "paypal.com",
            "billing@",
            "invoice@",
            "rechnung@",
        )
    )
    has_attachment = payload is not None and has_invoice_attachment(payload)

    strong_signal = (
        has_invoice_id
        or has_amount
        or (
            has_loose_amount
            and (has_invoice_id or known_billing_sender or has_payment_confirmation)
        )
        or (
            has_attachment
            and (has_invoice_subject or has_invoice_body or known_billing_sender)
        )
        or (known_billing_sender and (has_invoice_subject or has_payment_confirmation or has_amount))
    )
    if not strong_signal:
        return False

    return True


def list_all_message_ids(gmail_service) -> list[str]:
    message_ids: list[str] = []
    page_token = None
    while True:
        result = gmail_service.users().messages().list(
            userId="me",
            maxResults=500,
            pageToken=page_token,
        ).execute()
        message_ids.extend(item["id"] for item in result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return message_ids


def fetch_invoice_messages(
    gmail_service,
    full_inbox: bool = True,
    *,
    processed_label: str = "R-Verarbeitet",
    skip_processed: bool = True,
    reprocess_if_pdfs_remain: bool = True,
    gmail_queries: list[str] | None = None,
    pdf_ocr: bool = True,
) -> list[dict]:
    from core.google.invoice.enrich import collect_message_pdf_text, combine_extraction_text

    seen_ids: set[str] = set()
    messages: list[dict] = []
    processed_label_id = resolve_label_id(gmail_service, processed_label) if skip_processed else None
    queries = gmail_queries or resolve_gmail_queries()

    if full_inbox:
        candidate_ids = list_all_message_ids(gmail_service)
        print(f"[INFO] Vollscan: {len(candidate_ids)} E-Mail(s) im Postfach.")
    else:
        candidate_ids = []
        exclude = f"-label:{processed_label}" if skip_processed else ""
        print(f"[INFO] Gmail-Queries ({len(queries)}): Steuer-Scan …")
        for query in queries:
            q = query
            if skip_processed and "bezahldienst" not in query.lower():
                q = f"{query} {exclude}".strip()
            page_token = None
            while True:
                result = gmail_service.users().messages().list(
                    userId="me",
                    q=q,
                    maxResults=100,
                    pageToken=page_token,
                ).execute()
                candidate_ids.extend(item["id"] for item in result.get("messages", []))
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
        print(f"[INFO] Query-Scan: {len(candidate_ids)} eindeutige E-Mail-ID(s).")

    skipped = 0
    reprocessed = 0
    for message_id in candidate_ids:
        if message_id in seen_ids:
            continue
        seen_ids.add(message_id)

        message = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        headers = {
            header["name"].lower(): header["value"]
            for header in message["payload"].get("headers", [])
        }
        subject = headers.get("subject", "")
        sender = headers.get("from", "")
        date_header = headers.get("date", "")
        bundle_mail = is_invoice_bundle(subject, message["payload"])

        if skip_processed and is_message_processed(message, processed_label_id) and not bundle_mail:
            if reprocess_if_pdfs_remain:
                from core.google.invoice.mime import collect_pdf_attachments

                if collect_pdf_attachments(gmail_service, message_id, message["payload"]):
                    reprocessed += 1
                else:
                    skipped += 1
                    continue
            else:
                skipped += 1
                continue

        body = extract_all_text(gmail_service, message_id, message["payload"])
        if not body.strip():
            body = get_message_body(message["payload"])

        config = _load_invoice_config()
        if is_invoice_bundle(subject, message["payload"]):
            expanded = expand_invoice_bundle(
                gmail_service,
                message_id,
                message["payload"],
                parent_date_header=date_header,
                config=config,
                pdf_ocr=pdf_ocr,
            )
            if expanded:
                print(
                    f"[INFO] Sammelmail «{subject[:60]}»: "
                    f"{len(expanded)} Rechnung(en) aus {count_bundle_eml_attachments(message['payload'])} .eml"
                )
                messages.extend(expanded)
            continue

        pdf_text = collect_message_pdf_text(
            gmail_service,
            message_id,
            message["payload"],
            ocr=pdf_ocr,
        )
        combined_body = combine_extraction_text(body, pdf_text)

        if not is_invoice_candidate(subject, sender, combined_body, message["payload"]):
            continue

        messages.append(
            {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "date_header": date_header,
                "body": body,
                "pdf_text": pdf_text,
                "payload": message["payload"],
            }
        )

    if skipped:
        print(f"[INFO] {skipped} E-Mail(s) übersprungen (Label {processed_label}).")
    if reprocessed:
        print(
            f"[INFO] {reprocessed} bereits verarbeitete E-Mail(s) erneut "
            f"(PDF-Anhänge in verschachtelten .eml)."
        )
    return messages


def merge_invoice_rows(rows: list[InvoiceRow]) -> list[InvoiceRow]:
    merged: list[InvoiceRow] = []

    def same_vendor(left: InvoiceRow, right: InvoiceRow) -> bool:
        return left.vendor.split("(")[0].strip().lower() == right.vendor.split("(")[0].strip().lower()

    for row in rows:
        match = None
        for index, existing in enumerate(merged):
            if row.invoice_id and existing.invoice_id == row.invoice_id:
                match = index
                break
            if not row.invoice_id and not existing.invoice_id and same_vendor(row, existing):
                match = index
                break
            if row.invoice_id and same_vendor(row, existing) and not existing.amount:
                match = index
                break
            if existing.invoice_id and same_vendor(row, existing) and not row.invoice_id:
                match = index
                break

        if match is None:
            merged.append(row)
            continue

        existing = merged[match]
        merged[match] = InvoiceRow(
            vendor=existing.vendor or row.vendor,
            purpose=existing.purpose or row.purpose,
            amount=existing.amount or row.amount,
            interval=existing.interval or row.interval,
            contract_start=existing.contract_start or row.contract_start,
            next_renewal=existing.next_renewal or row.next_renewal,
            cancellation_days=existing.cancellation_days or row.cancellation_days,
            last_cancel_date=existing.last_cancel_date or row.last_cancel_date,
            payment_method=existing.payment_method or row.payment_method,
            invoice_id=existing.invoice_id or row.invoice_id,
            status=existing.status or row.status,
            source_message_id=existing.source_message_id or row.source_message_id,
            drive_url=existing.drive_url or row.drive_url,
            drive_path=existing.drive_path or row.drive_path,
        )

    return merged


def message_to_invoice_row(message: dict, *, pdf_text: str = "") -> InvoiceRow:
    from core.google.invoice.enrich import combine_extraction_text

    subject = message["subject"]
    sender = message["sender"]
    body = message["body"]
    pdf_text = pdf_text or str(message.get("pdf_text") or "")
    text = combine_extraction_text(body, pdf_text)
    invoice_id = extract_invoice_id(text, subject) or extract_invoice_id(body, subject)
    has_hint = bool(invoice_id or _sender_vendor_hint(sender))

    return InvoiceRow(
        vendor=infer_vendor(subject, sender, text),
        purpose=extract_purpose(text, subject),
        amount=extract_amount(text, strict=True)
        or extract_amount(text, strict=False)
        or (extract_amount(body, strict=True) if has_hint else "")
        or (extract_amount(body, strict=False) if has_hint else ""),
        interval=infer_interval(text, subject),
        contract_start=extract_contract_date(text, message["date_header"])
        or extract_contract_date(body, message["date_header"]),
        next_renewal=extract_next_renewal(text),
        cancellation_days=extract_cancellation_days(text),
        last_cancel_date="",
        payment_method=extract_payment_method(text) or extract_payment_method(body),
        invoice_id=invoice_id,
        status="Prüfen",
        source_message_id=message["id"],
    )


def read_existing_invoice_ids(sheets_service, *, spreadsheet_id: str | None = None) -> set[str]:
    sid = spreadsheet_id or SPREADSHEET_ID
    range_name = f"{SHEET_NAME}!J{DATA_START_ROW}:J"
    result = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=range_name)
        .execute()
    )
    existing: set[str] = set()
    for row in result.get("values", []):
        if row and row[0].strip():
            existing.add(row[0].strip())
    return existing


def find_first_empty_row(sheets_service, *, spreadsheet_id: str | None = None) -> int:
    sid = spreadsheet_id or SPREADSHEET_ID
    range_name = f"{SHEET_NAME}!A{DATA_START_ROW}:A"
    result = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=range_name)
        .execute()
    )
    values = result.get("values", [])
    for index, row in enumerate(values):
        if not row or not str(row[0]).strip():
            return DATA_START_ROW + index
    return DATA_START_ROW + len(values)


def update_drive_urls(
    sheets_service, rows: list[InvoiceRow], *, spreadsheet_id: str | None = None
) -> int:
    """Spalte L (Drive-Link) für bestehende Zeilen aktualisieren, wenn noch leer."""
    sid = spreadsheet_id or SPREADSHEET_ID
    if not rows:
        return 0
    range_name = f"{SHEET_NAME}!A{DATA_START_ROW}:L"
    result = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=sid, range=range_name)
        .execute()
    )
    values = result.get("values", [])
    updates: list[dict] = []
    for row in rows:
        if not row.drive_url:
            continue
        target_idx = None
        for idx, sheet_row in enumerate(values):
            while len(sheet_row) < 12:
                sheet_row.append("")
            col_j = (sheet_row[9] or "").strip()
            col_a = (sheet_row[0] or "").strip()
            col_l = (sheet_row[11] or "").strip()
            if col_l:
                continue
            if row.invoice_id and col_j == row.invoice_id:
                target_idx = idx
                break
            if not row.invoice_id and col_a and col_a == row.vendor:
                target_idx = idx
                break
        if target_idx is not None:
            sheet_row_num = DATA_START_ROW + target_idx
            updates.append(
                {
                    "range": f"{SHEET_NAME}!L{sheet_row_num}",
                    "values": [[row.drive_url]],
                }
            )
    if not updates:
        return 0
    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=sid,
        body={"valueInputOption": "USER_ENTERED", "data": updates},
    ).execute()
    return len(updates)


def write_rows(
    sheets_service,
    start_row: int,
    rows: list[InvoiceRow],
    *,
    spreadsheet_id: str | None = None,
) -> None:
    sid = spreadsheet_id or SPREADSHEET_ID
    if not rows:
        return
    end_row = start_row + len(rows) - 1
    range_name = f"{SHEET_NAME}!A{start_row}:L{end_row}"
    body = {"values": [row.to_sheet_row() for row in rows]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sid,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()


def main() -> None:
    print("=" * 60)
    print(" Rechnungen aus Gmail extrahieren ".center(60, "="))
    print("=" * 60)

    creds = load_credentials()
    gmail_service = build("gmail", "v1", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    try:
        messages = fetch_invoice_messages(gmail_service)
        print(f"[INFO] {len(messages)} Rechnungs-E-Mail(s) gefunden.")

        invoice_rows = merge_invoice_rows([message_to_invoice_row(message) for message in messages])
        existing_ids = read_existing_invoice_ids(sheets_service)
        new_rows = [
            row
            for row in invoice_rows
            if not row.invoice_id or row.invoice_id not in existing_ids
        ]

        if not new_rows:
            print("[INFO] Keine neuen Rechnungszeilen zum Eintragen.")
            for row in invoice_rows:
                print(
                    f"  - {row.vendor} | {row.amount or '?'} EUR | "
                    f"Rechnung {row.invoice_id or 'n/a'} | {row.contract_start}"
                )
            return

        start_row = find_first_empty_row(sheets_service)
        write_rows(sheets_service, start_row, new_rows)

        print(f"[ERFOLG] {len(new_rows)} Zeile(n) ab Zeile {start_row} eingetragen:")
        for row in new_rows:
            print(
                f"  - {row.vendor} | {row.amount or '?'} EUR | "
                f"Rechnung {row.invoice_id or 'n/a'} | {row.contract_start}"
            )
        print(
            f"\nSheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
        )
    except HttpError as error:
        print(f"[FEHLER] Google API: {error}")
    except Exception as error:
        print(f"[FEHLER] {error}")


if __name__ == "__main__":
    main()
