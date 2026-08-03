"""Rechnungs-Text anreichern — E-Mail-Body + PDF/OCR für Sheet-Felder."""

from __future__ import annotations

from core.google.invoice.mime import collect_pdf_attachments, pdfs_from_parsed_message
from core.google.invoice.pdf_text import texts_from_pdf_attachments


def combine_extraction_text(body: str, pdf_text: str) -> str:
    parts = [body.strip()]
    if pdf_text.strip():
        parts.append(pdf_text.strip())
    return "\n\n".join(part for part in parts if part)


def collect_message_pdf_text(
    gmail_service,
    message_id: str,
    payload: dict | None,
    *,
    parsed_eml=None,
    ocr: bool = True,
) -> str:
    """PDF-Anhänge einer Nachricht als kombinierten Text."""
    if parsed_eml is not None:
        pdfs = pdfs_from_parsed_message(parsed_eml)
    elif payload and gmail_service:
        parent_id = message_id.split("#", 1)[0]
        pdfs = collect_pdf_attachments(gmail_service, parent_id, payload)
    else:
        pdfs = []
    return texts_from_pdf_attachments(pdfs, ocr=ocr)


def invoice_row_from_message(
    gmail_service,
    message: dict,
    row_factory,
    *,
    ocr: bool = True,
):
    """InvoiceRow mit PDF/OCR-angereichertem Text."""
    pdf_text = collect_message_pdf_text(
        gmail_service,
        message["id"],
        message.get("payload"),
        parsed_eml=message.get("parsed_eml"),
        ocr=ocr,
    )
    return row_factory(message, pdf_text=pdf_text)
