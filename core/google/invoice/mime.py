"""MIME-Helfer — verschachtelte .eml / message/rfc822 und PDF-Sammlung."""
from __future__ import annotations

import base64
import email
import re
from email import policy
from email.message import Message

import html as html_module

_MAX_NEST_DEPTH = 8


def _decode_gmail_data(part: dict) -> bytes | None:
    data = part.get("body", {}).get("data")
    if not data:
        return None
    return base64.urlsafe_b64decode(data)


def _html_to_text(raw: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", html_module.unescape(raw))
    return re.sub(r"\s+", " ", cleaned).strip()


def _looks_like_rfc822_bytes(raw: bytes) -> bool:
    head = raw[:4096].lower()
    if raw[:5] == b"%PDF-":
        return False
    if b"mime-version:" in head and (
        b"subject:" in head or b"from:" in head or b"content-type:" in head
    ):
        return True
    return b"from:" in head and (b"subject:" in head or b"mime-version:" in head)


def _unwrap_base64_eml(msg: Message) -> Message | None:
    """Base64-kodierte .eml in text/plain (typisch bei message/rfc822 in .eml)."""
    for sub in msg.walk():
        if sub.get_content_type() != "text/plain":
            continue
        body = sub.get_payload()
        if not isinstance(body, str) or len(body) < 40:
            continue
        try:
            cleaned = re.sub(r"\s+", "", body)
            decoded = base64.b64decode(cleaned)
        except Exception:
            continue
        if _looks_like_rfc822_bytes(decoded):
            return _parse_email_bytes(decoded)
    return None


def _nested_message_from_part(part) -> Message | None:
    """Verschachtelte E-Mail aus email.message-Part extrahieren."""
    nested: Message | None = None
    try:
        payload = part.get_payload(0)
        if isinstance(payload, Message):
            nested = payload
        elif isinstance(payload, str):
            nested = _parse_email_bytes(payload.encode("utf-8", errors="replace"))
    except Exception:
        pass

    if nested is None:
        raw = part.get_payload(decode=True)
        if isinstance(raw, str):
            raw = raw.encode("utf-8", errors="replace")
        if raw:
            nested = _parse_email_bytes(raw)

    if nested is None:
        return None

    unwrapped = _unwrap_base64_eml(nested)
    return unwrapped or nested


def _parse_email_bytes(raw: bytes) -> Message | None:
    if not raw or len(raw) < 20:
        return None
    try:
        return email.message_from_bytes(raw, policy=policy.default)
    except Exception:
        if _looks_like_rfc822_bytes(raw):
            try:
                return email.message_from_bytes(raw, policy=policy.compat32)
            except Exception:
                return None
        return None


def _parse_downloaded_eml(raw: bytes) -> Message | None:
    msg = _parse_email_bytes(raw)
    if not msg:
        return None
    return _unwrap_base64_eml(msg) or msg


def _is_nested_email_part(part: dict) -> bool:
    filename = (part.get("filename") or "").lower()
    mime = (part.get("mimeType") or "").lower()
    if filename.endswith(".eml"):
        return True
    if mime in ("message/rfc822", "application/vnd.ms-outlook"):
        return True
    if mime == "application/octet-stream" and filename.endswith(".eml"):
        return True
    if re.search(r"rechnung|invoice|receipt|beleg|mail", filename, re.IGNORECASE):
        if mime.startswith("message/") or mime == "application/octet-stream":
            return True
    return False


def _is_pdf_part(part: dict) -> bool:
    filename = (part.get("filename") or "").lower()
    mime = (part.get("mimeType") or "").lower()
    return filename.endswith(".pdf") or mime == "application/pdf"


def _texts_from_email_message(msg: Message) -> list[str]:
    texts: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                ctype = part.get_content_type()
                if ctype not in ("message/rfc822",) and not (
                    part.get_filename() or ""
                ).lower().endswith(".eml"):
                    continue
            ctype = part.get_content_type()
            try:
                payload = part.get_content()
            except Exception:
                continue
            if not payload:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", errors="replace")
            if ctype == "text/plain":
                texts.append(str(payload))
            elif ctype == "text/html":
                texts.append(_html_to_text(str(payload)))
            elif ctype == "message/rfc822" or (part.get_filename() or "").lower().endswith(".eml"):
                nested = _nested_message_from_part(part)
                if nested:
                    texts.extend(_texts_from_email_message(nested))
    else:
        try:
            payload = msg.get_content()
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                texts.append(_html_to_text(str(payload)))
            else:
                texts.append(str(payload))
        except Exception:
            pass
    return texts


def _pdfs_from_email_message(msg: Message, depth: int = 0) -> list[tuple[str, bytes]]:
    """PDFs aus parsed email.message (beliebig verschachtelt)."""
    if depth > _MAX_NEST_DEPTH:
        return []
    out: list[tuple[str, bytes]] = []

    for part in msg.walk():
        filename = part.get_filename() or ""
        ctype = part.get_content_type()
        disp = part.get_content_disposition()

        if filename.lower().endswith(".pdf") or ctype == "application/pdf":
            try:
                data = part.get_payload(decode=True)
                if data:
                    out.append((filename or "Rechnung.pdf", data))
            except Exception:
                pass
            continue

        is_nested = (
            filename.lower().endswith(".eml")
            or ctype == "message/rfc822"
            or ctype == "application/vnd.ms-outlook"
        )
        if is_nested or (disp == "attachment" and _looks_like_rfc822_bytes(
            part.get_payload(decode=True) or b""
        )):
            nested_msg = _nested_message_from_part(part)
            if nested_msg:
                for fn, data in _pdfs_from_email_message(nested_msg, depth + 1):
                    out.append((fn, data))

    return out


def _download_attachment(gmail_service, message_id: str, att_id: str) -> bytes:
    att = (
        gmail_service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=message_id, id=att_id)
        .execute()
    )
    return base64.urlsafe_b64decode(att["data"])


def _collect_from_parsed_email(msg: Message, add) -> None:
    for fn, data in _pdfs_from_email_message(msg):
        add(fn, data)


def pdfs_from_parsed_message(msg: Message) -> list[tuple[str, bytes]]:
    """PDF-Anhänge aus bereits geparster E-Mail (z. B. .eml in Sammelmail)."""
    return _pdfs_from_email_message(msg)


def texts_from_parsed_message(msg: Message) -> str:
    chunks = _texts_from_email_message(msg)
    combined = "\n".join(c for c in chunks if c.strip())
    return re.sub(r"\n{3,}", "\n\n", combined).strip()


def list_bundle_eml_attachments(
    gmail_service, message_id: str, payload: dict
) -> list[dict]:
    """
    Top-level .eml/message/rfc822-Anhänge einer Sammelmail (z. B. «Rechnungen aus Bezahldienste»).
    Returns: [{index, filename, parsed, parent_message_id}, ...]
    """
    results: list[dict] = []
    for index, part in enumerate(payload.get("parts") or []):
        mime = (part.get("mimeType") or "").lower()
        if not (_is_nested_email_part(part) or mime == "message/rfc822"):
            continue

        filename = part.get("filename") or f"nested_{index}.eml"
        att_id = part.get("body", {}).get("attachmentId")
        raw: bytes | None = None
        if att_id:
            try:
                raw = _download_attachment(gmail_service, message_id, att_id)
            except Exception:
                continue
        else:
            raw = _decode_gmail_data(part)
        if not raw:
            continue

        parsed = _parse_downloaded_eml(raw)
        if not parsed:
            continue

        results.append(
            {
                "index": index,
                "filename": filename,
                "parsed": parsed,
                "raw_bytes": raw,
                "parent_message_id": message_id,
            }
        )
    return results


def count_bundle_eml_attachments(payload: dict) -> int:
    return sum(
        1
        for part in payload.get("parts") or []
        if _is_nested_email_part(part) or (part.get("mimeType") or "") == "message/rfc822"
    )


def collect_pdf_attachments(gmail_service, message_id: str, payload: dict) -> list[tuple[str, bytes]]:
    """
    Sammelt PDF-Dokumente — direkt und aus verschachtelten .eml / message/rfc822
    (auch Bezahldienste: .eml mit attachmentId, mehrfach verschachtelt).
    Returns: [(filename, bytes), ...]
    """
    results: list[tuple[str, bytes]] = []
    seen: set[tuple[str, int]] = set()

    def add(name: str, data: bytes) -> None:
        key = (name, len(data))
        if key in seen or not data:
            return
        seen.add(key)
        results.append((name, data))

    def walk_part(part: dict, depth: int = 0) -> None:
        if depth > _MAX_NEST_DEPTH:
            return

        mime = part.get("mimeType", "")
        filename = part.get("filename") or ""
        att_id = part.get("body", {}).get("attachmentId")

        # PDF direkt
        if att_id and _is_pdf_part(part):
            try:
                add(filename or "Rechnung.pdf", _download_attachment(gmail_service, message_id, att_id))
            except Exception:
                pass
            return

        # Verschachtelte E-Mail — attachmentId ZUERST (Gmail/Bezahldienste)
        if _is_nested_email_part(part):
            if att_id:
                try:
                    raw = _download_attachment(gmail_service, message_id, att_id)
                    nested = _parse_downloaded_eml(raw)
                    if nested:
                        _collect_from_parsed_email(nested, add)
                except Exception:
                    pass
            raw_inline = _decode_gmail_data(part)
            if raw_inline:
                nested = _parse_downloaded_eml(raw_inline)
                if nested:
                    _collect_from_parsed_email(nested, add)
            for child in part.get("parts", []) or []:
                walk_part(child, depth + 1)
            return

        # message/rfc822 ohne Dateiname (inline)
        if mime == "message/rfc822":
            if att_id:
                try:
                    raw = _download_attachment(gmail_service, message_id, att_id)
                    nested = _parse_downloaded_eml(raw)
                    if nested:
                        _collect_from_parsed_email(nested, add)
                except Exception:
                    pass
            raw_inline = _decode_gmail_data(part)
            if raw_inline:
                nested = _parse_downloaded_eml(raw_inline)
                if nested:
                    _collect_from_parsed_email(nested, add)
            for child in part.get("parts", []) or []:
                walk_part(child, depth + 1)
            return

        # Unbekannter Anhang — versuche als .eml zu parsen
        if att_id and filename and not _is_pdf_part(part):
            try:
                raw = _download_attachment(gmail_service, message_id, att_id)
                if _looks_like_rfc822_bytes(raw):
                    nested = _parse_downloaded_eml(raw)
                    if nested:
                        _collect_from_parsed_email(nested, add)
                        return
            except Exception:
                pass

        for child in part.get("parts", []) or []:
            walk_part(child, depth + 1)

    walk_part(payload)
    return results


def extract_all_text(gmail_service, message_id: str, payload: dict) -> str:
    """Body-Text inkl. verschachtelter E-Mails für Feld-Extraktion."""
    chunks: list[str] = []

    def walk_part(part: dict, depth: int = 0) -> None:
        if depth > _MAX_NEST_DEPTH:
            return

        mime = part.get("mimeType", "")
        att_id = part.get("body", {}).get("attachmentId")
        filename = part.get("filename") or ""

        def absorb_nested(raw: bytes) -> None:
            nested = _parse_downloaded_eml(raw)
            if nested:
                chunks.extend(_texts_from_email_message(nested))

        if _is_nested_email_part(part) or mime == "message/rfc822":
            if att_id:
                try:
                    absorb_nested(_download_attachment(gmail_service, message_id, att_id))
                except Exception:
                    pass
            raw_inline = _decode_gmail_data(part)
            if raw_inline:
                absorb_nested(raw_inline)
            for child in part.get("parts", []) or []:
                walk_part(child, depth + 1)
            return

        if att_id and not _is_pdf_part(part):
            try:
                raw = _download_attachment(gmail_service, message_id, att_id)
                if _looks_like_rfc822_bytes(raw):
                    absorb_nested(raw)
            except Exception:
                pass
        elif not att_id:
            data = part.get("body", {}).get("data")
            if data:
                raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                if mime == "text/plain":
                    chunks.append(raw)
                elif mime == "text/html":
                    chunks.append(_html_to_text(raw))

        for child in part.get("parts", []) or []:
            walk_part(child, depth + 1)

    walk_part(payload)
    combined = "\n".join(c for c in chunks if c.strip())
    return re.sub(r"\n{3,}", "\n\n", combined).strip()


def has_invoice_attachment(payload: dict) -> bool:
    """PDF, .eml, message/rfc822 oder verschachtelte Rechnungs-Anhänge."""

    def walk(part: dict, depth: int = 0) -> bool:
        if depth > _MAX_NEST_DEPTH:
            return False
        filename = part.get("filename") or ""
        mime = part.get("mimeType", "")
        lower = filename.lower()
        if lower.endswith(".pdf") or lower.endswith(".eml"):
            return True
        if mime in ("message/rfc822", "application/pdf", "application/vnd.ms-outlook"):
            return True
        if re.search(r"rechnung|invoice|receipt|beleg", filename, re.IGNORECASE):
            return True
        att_id = part.get("body", {}).get("attachmentId")
        if att_id and _is_nested_email_part(part):
            return True
        for child in part.get("parts", []) or []:
            if walk(child, depth + 1):
                return True
        return False

    return walk(payload)
