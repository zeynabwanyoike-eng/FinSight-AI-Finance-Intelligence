
from decimal import Decimal
from database.invoice_database import get_connection
from app.payment_manager import create_payment_table


def get_supplier_analytics():
    create_payment_table()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                i.supplier,
                COUNT(DISTINCT i.id) AS invoice_count,
                SUM(i.total) AS total_invoiced,
                COALESCE(SUM(p.amount), 0) AS total_paid
            FROM invoices i
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) AS amount
                FROM invoice_payments
                GROUP BY invoice_id
            ) p ON i.id = p.invoice_id
            GROUP BY i.supplier
            ORDER BY total_invoiced DESC
        """).fetchall()

        results = []

        for row in rows:
            invoiced = Decimal(str(row["total_invoiced"] or 0))
            paid = Decimal(str(row["total_paid"] or 0))

            results.append({
                "supplier": row["supplier"],
                "invoice_count": row["invoice_count"],
                "total_invoiced": str(invoiced),
                "total_paid": str(paid),
                "outstanding": str(invoiced - paid)
            })

        return results


if __name__ == "__main__":
    print("===== SUPPLIER FINANCIAL ANALYTICS =====")

    for supplier in get_supplier_analytics():
        print(supplier)
