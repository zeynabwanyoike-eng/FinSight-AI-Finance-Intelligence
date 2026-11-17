
from decimal import Decimal
from database.invoice_database import get_connection


def reconcile_payments():
    """
    Compare invoice totals against recorded payments.

    This function is read-only. It does not modify invoices
    or existing payment records.
    """

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                i.id AS invoice_id,
                i.supplier,
                i.invoice_number,
                i.invoice_date,
                i.total AS invoice_total,
                i.processing_status,
                COALESCE(SUM(p.amount), 0) AS amount_paid,
                COUNT(p.id) AS payment_count
            FROM invoices AS i
            LEFT JOIN invoice_payments AS p
                ON i.id = p.invoice_id
            GROUP BY
                i.id,
                i.supplier,
                i.invoice_number,
                i.invoice_date,
                i.total,
                i.processing_status
            ORDER BY i.id DESC
        """).fetchall()

    results = []

    for row in rows:
        total = Decimal(str(row["invoice_total"] or 0))
        paid = Decimal(str(row["amount_paid"] or 0))
        outstanding = total - paid

        if paid > total:
            status = "OVERPAID"
        elif paid == total and total > 0:
            status = "PAID"
        elif paid > 0:
            status = "PARTIALLY_PAID"
        else:
            status = "UNPAID"

        results.append({
            "invoice_id": row["invoice_id"],
            "supplier": row["supplier"],
            "invoice_number": row["invoice_number"],
            "invoice_date": row["invoice_date"],
            "invoice_total": float(total),
            "amount_paid": float(paid),
            "outstanding_balance": float(outstanding),
            "payment_count": row["payment_count"],
            "processing_status": row["processing_status"],
            "reconciliation_status": status
        })

    return results


def get_reconciliation_summary():
    records = reconcile_payments()

    return {
        "total_invoices": len(records),
        "paid": sum(
            r["reconciliation_status"] == "PAID"
            for r in records
        ),
        "partially_paid": sum(
            r["reconciliation_status"] == "PARTIALLY_PAID"
            for r in records
        ),
        "unpaid": sum(
            r["reconciliation_status"] == "UNPAID"
            for r in records
        ),
        "overpaid": sum(
            r["reconciliation_status"] == "OVERPAID"
            for r in records
        ),
        "total_invoiced": sum(
            r["invoice_total"] for r in records
        ),
        "total_paid": sum(
            r["amount_paid"] for r in records
        ),
        "total_outstanding": sum(
            r["outstanding_balance"] for r in records
        )
    }
