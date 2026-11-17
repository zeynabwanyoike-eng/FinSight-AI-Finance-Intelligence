
def normalize(value):
    return str(value).strip().casefold()


def check_duplicate(invoice, existing_invoices):
    supplier = invoice.get("supplier")
    invoice_number = invoice.get("invoice_number")

    if not supplier or not invoice_number:
        return {
            "duplicate": False,
            "status": "REQUIRES_REVIEW",
            "message": "Supplier or invoice number is missing."
        }

    for existing in existing_invoices:
        same_supplier = (
            normalize(supplier) == normalize(existing.get("supplier", ""))
        )

        same_number = (
            normalize(invoice_number) ==
            normalize(existing.get("invoice_number", ""))
        )

        if same_supplier and same_number:
            return {
                "duplicate": True,
                "status": "DUPLICATE_FLAGGED",
                "message": "This invoice already exists."
            }

    return {
        "duplicate": False,
        "status": "UNIQUE",
        "message": "No matching invoice found."
    }


if __name__ == "__main__":
    existing = [
        {
            "supplier": "ABC Supplies",
            "invoice_number": "INV-001"
        }
    ]

    new_invoice = {
        "supplier": "ABC Supplies",
        "invoice_number": "INV-001"
    }

    print(check_duplicate(new_invoice, existing))
