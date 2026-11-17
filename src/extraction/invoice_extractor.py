
import re
from pathlib import Path
from io import BytesIO

import pymupdf
import pytesseract
from PIL import Image


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


CURRENCY_PATTERN = (
    r"(?:KES|KSh|USD|EUR|GBP|£|\$)"
)

AMOUNT_PATTERN = r"\d[\d,]*(?:\.\d{1,2})?"


def extract_invoice_text(pdf_path):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Invoice PDF not found: {pdf_path}"
        )

    extracted_pages = []

    with pymupdf.open(pdf_path) as document:
        for page in document:
            text = page.get_text("text").strip()

            if len(text) < 20:
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False
                )

                image = Image.open(
                    BytesIO(pixmap.tobytes("png"))
                )

                text = pytesseract.image_to_string(
                    image,
                    lang="eng"
                ).strip()

            extracted_pages.append(text)

    return "\n".join(extracted_pages).strip()


def extract_invoice_details(text):
    if not text or not text.strip():
        return {
            "supplier": None,
            "invoice_number": None,
            "invoice_date": None,
            "total": None,
            "amounts_found": [],
            "status": "NO_TEXT_FOUND",
            "message": "No readable invoice text was found."
        }

    supplier_match = re.search(
        r"(?:Supplier|Vendor|From)\s*:\s*(.+)",
        text,
        re.IGNORECASE
    )

    supplier = (
        supplier_match.group(1).strip()
        if supplier_match
        else None
    )

    invoice_number_match = re.search(
        r"(?:Invoice\s*(?:Number|No\.?|#)|Invoice#)"
        r"\s*[:#]?\s*([A-Z0-9][A-Z0-9\-\/]+)",
        text,
        re.IGNORECASE
    )

    invoice_number = (
        invoice_number_match.group(1).strip()
        if invoice_number_match
        else None
    )

    date_match = re.search(
        r"\b(?:\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}"
        r"|\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b",
        text
    )

    invoice_date = (
        date_match.group(0)
        if date_match
        else None
    )

    total_pattern = (
        r"\b(?:GRAND\s+TOTAL|TOTAL\s+DUE|"
        r"AMOUNT\s+DUE|BALANCE\s+DUE|TOTAL)"
        r"\b\s*[:\-]?\s*"
        r"(" + CURRENCY_PATTERN + r")?\s*"
        r"(" + AMOUNT_PATTERN + r")"
    )

    total_match = re.search(
        total_pattern,
        text,
        re.IGNORECASE
    )

    total = None

    if total_match:
        total = total_match.group(2).replace(",", "")

    amount_pattern = (
        CURRENCY_PATTERN + r"\s*" + AMOUNT_PATTERN
    )

    amounts_found = re.findall(
        amount_pattern,
        text,
        re.IGNORECASE
    )

    # Put the labelled invoice total first so the existing
    # processing pipeline uses it instead of a unit price.
    if total_match:
        total_currency = total_match.group(1) or ""
        total_amount = total_match.group(2)

        total_display = (
            f"{total_currency} {total_amount}".strip()
        )

        amounts_found = [
            total_display
        ] + [
            amount for amount in amounts_found
            if amount != total_display
        ]

    return {
        "supplier": supplier,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "total": total,
        "amounts_found": amounts_found,
        "status": "EXTRACTED"
    }


def extract_invoice_from_pdf(pdf_path):
    try:
        text = extract_invoice_text(pdf_path)

        if not text:
            return {
                "supplier": None,
                "invoice_number": None,
                "invoice_date": None,
                "total": None,
                "amounts_found": [],
                "status": "NO_TEXT_FOUND",
                "message": (
                    "No readable text was found. "
                    "Please check the PDF quality."
                )
            }

        return extract_invoice_details(text)

    except Exception as error:
        return {
            "supplier": None,
            "invoice_number": None,
            "invoice_date": None,
            "total": None,
            "amounts_found": [],
            "status": "EXTRACTION_ERROR",
            "message": str(error)
        }


if __name__ == "__main__":
    sample_pdf = (
        "data/sample_invoices/scanned_invoice.pdf"
    )

    result = extract_invoice_from_pdf(sample_pdf)

    print("\n===== INVOICE EXTRACTION REPORT =====")
    print(result)
