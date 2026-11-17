from decimal import Decimal, InvalidOperation
from database.invoice_database import get_connection


def create_payment_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_reference TEXT UNIQUE NOT NULL,
                recorded_by TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        """)


def record_payment(invoice_id, amount, reference, recorded_by):
    create_payment_table()

    try:
        payment_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return {"success": False, "message": "Invalid payment amount."}

    if not payment_amount.is_finite() or payment_amount <= 0:
        return {"success": False, "message": "Payment must be greater than zero."}

    reference = str(reference).strip() if reference is not None else ""
    recorded_by = str(recorded_by).strip() if recorded_by is not None else ""

    if not reference:
        return {"success": False, "message": "Payment reference is required."}

    if not recorded_by:
        return {"success": False, "message": "Recorded-by name is required."}

    with get_connection() as conn:
        invoice = conn.execute(
            "SELECT total, processing_status FROM invoices WHERE id = ?",
            (invoice_id,)
        ).fetchone()

        if invoice is None:
            return {"success": False, "message": "Invoice not found."}

        if invoice["processing_status"] != "APPROVED":
            return {"success": False, "message": "Only approved invoices can be paid."}

        paid = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM invoice_payments
            WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()[0]

        total = Decimal(str(invoice["total"]))
        outstanding = total - Decimal(str(paid))

        if payment_amount > outstanding:
            return {
                "success": False,
                "message": f"Overpayment rejected. Outstanding balance: {outstanding}"
            }

        try:
            conn.execute("""
                INSERT INTO invoice_payments
                (invoice_id, amount, payment_reference, recorded_by)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, float(payment_amount), reference, recorded_by))
        except Exception as error:
            return {"success": False, "message": f"Payment not recorded: {error}"}

        new_balance = outstanding - payment_amount

        return {
            "success": True,
            "invoice_id": invoice_id,
            "amount_paid": str(payment_amount),
            "outstanding_balance": str(new_balance),
            "payment_status": "PAID" if new_balance == 0 else "PARTIALLY_PAID"
        }


def get_payment_summary(invoice_id):
    create_payment_table()

    with get_connection() as conn:
        invoice = conn.execute(
            "SELECT total FROM invoices WHERE id = ?",
            (invoice_id,)
        ).fetchone()

        if invoice is None:
            return None

        paid = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM invoice_payments
            WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()[0]

        total = Decimal(str(invoice["total"]))
        paid = Decimal(str(paid))

        return {
            "invoice_total": str(total),
            "amount_paid": str(paid),
            "outstanding_balance": str(total - paid),
            "payment_status": "PAID" if paid == total else (
                "PARTIALLY_PAID" if paid > 0 else "UNPAID"
            )
        }


def get_payment_history():
    """
    Return every recorded payment with its related invoice details.
    Existing payment records are read only; this function does not modify them.
    """
    create_payment_table()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                p.id AS payment_id,
                p.invoice_id,
                i.supplier,
                i.invoice_number,
                i.invoice_date,
                i.total AS invoice_total,
                p.amount AS payment_amount,
                p.payment_reference,
                p.recorded_by,
                p.created_at AS payment_date
            FROM invoice_payments AS p
            INNER JOIN invoices AS i
                ON i.id = p.invoice_id
            ORDER BY p.created_at DESC, p.id DESC
        """).fetchall()

        return [dict(row) for row in rows]


if __name__ == "__main__":
    print("Payment tracking module initialized.")
