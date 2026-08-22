"""PDF / document intelligence (spec section 22).

Extracts raw text from PDFs; falls back to OCR when the PDF has no text layer
(scanned tender documents are common). Never fabricates content - if extraction
yields nothing, callers must show "לא נמצא" rather than guessing.
"""

from dataclasses import dataclass
from io import BytesIO

import pdfplumber

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:  # OCR deps are optional at runtime; degrade gracefully
    OCR_AVAILABLE = False


@dataclass
class ExtractedDocument:
    text: str
    page_count: int
    ocr_used: bool


def extract_text_from_pdf_bytes(data: bytes, ocr_language: str = "heb+eng") -> ExtractedDocument:
    text_parts: list[str] = []
    page_count = 0
    with pdfplumber.open(BytesIO(data)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

    combined = "\n".join(text_parts).strip()
    ocr_used = False

    # If almost no text was extracted, the PDF is likely scanned -> run OCR.
    if len(combined) < 40 and OCR_AVAILABLE:
        ocr_used = True
        ocr_parts: list[str] = []
        images = convert_from_bytes(data)
        for image in images:
            ocr_parts.append(pytesseract.image_to_string(image, lang=ocr_language))
        combined = "\n".join(ocr_parts).strip()

    return ExtractedDocument(text=combined, page_count=page_count, ocr_used=ocr_used)
