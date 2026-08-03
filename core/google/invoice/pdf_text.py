"""PDF-Text für Rechnungs-Extraktion — pypdf + optional OCR für Scans."""

from __future__ import annotations

import io
import re

MIN_TEXT_LEN_BEFORE_OCR = 80


def extract_text_from_pdf_bytes(data: bytes, *, ocr: bool = True) -> str:
    """Text aus PDF-Bytes; bei wenig Text optional OCR (Tesseract)."""
    if not data or data[:5] == b"%PDF-" and len(data) < 32:
        return ""

    text = _extract_with_pypdf(data)
    if ocr and len(text.strip()) < MIN_TEXT_LEN_BEFORE_OCR:
        ocr_text = _extract_with_ocr(data)
        if len(ocr_text.strip()) > len(text.strip()):
            text = ocr_text
    return _normalize_pdf_text(text)


def texts_from_pdf_attachments(
    pdfs: list[tuple[str, bytes]],
    *,
    ocr: bool = True,
) -> str:
    parts: list[str] = []
    for name, data in pdfs:
        if not data:
            continue
        extracted = extract_text_from_pdf_bytes(data, ocr=ocr)
        if extracted:
            parts.append(f"--- PDF: {name} ---\n{extracted}")
    return "\n\n".join(parts)


def _normalize_pdf_text(text: str) -> str:
    cleaned = text.replace("\ufffd", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extract_with_pypdf(data: bytes) -> str:
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(data))
        pages: list[str] = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"--- Seite {idx + 1} ---\n{page_text}")
        return "\n\n".join(pages)
    except Exception:
        return ""


def _extract_with_ocr(data: bytes) -> str:
    """OCR-Fallback für gescannte PDFs (optional: pdf2image + pytesseract + Tesseract)."""
    try:
        import pdf2image
        import pytesseract

        images = pdf2image.convert_from_bytes(data, dpi=200, fmt="png")
        parts: list[str] = []
        for idx, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang="deu+eng") or ""
            if page_text.strip():
                parts.append(f"--- OCR Seite {idx + 1} ---\n{page_text}")
        return "\n\n".join(parts)
    except Exception:
        return ""
