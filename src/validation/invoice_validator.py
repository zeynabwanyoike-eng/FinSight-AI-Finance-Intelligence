
from decimal import Decimal, InvalidOperation


def validate_invoice(invoice):
    errors = []

    required_fields = ["invoice_number", "invoice_date", "total"]

    for field in required_fields:
        if not invoice.get(field):
            errors.append(f"Missing required field: {field}")

    if invoice.get("total") is not None:
        try:
            total = Decimal(str(invoice["total"]))

            if total <= 0:
                errors.append("Invoice total must be greater than zero.")

        except InvalidOperation:
            errors.append("Invoice total is not a valid number.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "status": "VALIDATED" if not errors else "REQUIRES_REVIEW"
    }


if __name__ == "__main__":
    sample_invoice = {
        "invoice_number": "INV-2026-001",
        "invoice_date": "15/11/2026",
        "total": "25000.00"
    }

    print(validate_invoice(sample_invoice))
