
import re

from src.extraction.invoice_extractor import (
    extract_invoice_details,
    extract_invoice_from_pdf
)

from src.validation.invoice_validator import validate_invoice
from src.validation.duplicate_detector import check_duplicate

from database.invoice_database import (
    initialize_database,
    save_invoice,
    get_all_invoices
)


def process_extracted_invoice(extracted):
    """
    Validate extracted invoice details, check duplicates,
    and save eligible invoices.
    """

    initialize_database()

    amounts = extracted.get("amounts_found", [])

    total = None

    if amounts:
        total = re.sub(r"[^\d.]", "", amounts[0])

    invoice = {
        "supplier": extracted.get("supplier"),
        "invoice_number": extracted.get("invoice_number"),
        "invoice_date": extracted.get("invoice_date"),
        "total": total
    }

    validation = validate_invoice(invoice)

    existing_invoices = get_all_invoices()

    duplicate = check_duplicate(
        invoice,
        existing_invoices
    )

    if not validation["valid"]:

        status = "REQUIRES_REVIEW"

    elif duplicate["duplicate"]:

        status = "DUPLICATE_FLAGGED"

    else:

        status = "READY_FOR_APPROVAL"

        save_invoice(invoice, status)

    return {
        "invoice": invoice,
        "validation": validation,
        "duplicate_check": duplicate,
        "final_status": status
    }


def process_invoice(raw_text):
    """
    Process invoice information supplied as text.
    """

    extracted = extract_invoice_details(raw_text)

    return process_extracted_invoice(extracted)


def process_invoice_pdf(pdf_path):
    """
    Extract and process an invoice directly from a PDF.
    """

    extracted = extract_invoice_from_pdf(pdf_path)

    if extracted.get("status") != "EXTRACTED":

        return {
            "invoice": None,
            "validation": None,
            "duplicate_check": None,
            "final_status": "REQUIRES_REVIEW",
            "message": extracted.get(
                "message",
                "Could not extract invoice information."
            )
        }

    return process_extracted_invoice(extracted)
