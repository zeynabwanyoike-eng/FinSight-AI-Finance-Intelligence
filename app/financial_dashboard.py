
from decimal import Decimal
from database.invoice_database import get_connection
from app.payment_manager import create_payment_table


def get_dashboard_metrics():
    create_payment_table()

    with get_connection() as conn:

        invoice_data = conn.execute("""
            SELECT
                COUNT(*) AS total_invoices,
                COALESCE(SUM(total), 0) AS total_invoiced,
                SUM(CASE WHEN processing_status = 'READY_FOR_APPROVAL'
                    THEN 1 ELSE 0 END) AS pending_approval,
                SUM(CASE WHEN processing_status = 'APPROVED'
                    THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN processing_status = 'REJECTED'
                    THEN 1 ELSE 0 END) AS rejected
            FROM invoices
        """).fetchone()

        payment_data = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total_paid
            FROM invoice_payments
        """).fetchone()

        supplier_data = conn.execute("""
            SELECT COUNT(DISTINCT supplier) AS total_suppliers
            FROM invoices
        """).fetchone()

        total_invoiced = Decimal(str(invoice_data["total_invoiced"]))
        total_paid = Decimal(str(payment_data["total_paid"]))

        return {
            "total_invoices": invoice_data["total_invoices"],
            "total_suppliers": supplier_data["total_suppliers"],
            "total_invoiced": str(total_invoiced),
            "total_paid": str(total_paid),
            "outstanding_balance": str(total_invoiced - total_paid),
            "pending_approval": invoice_data["pending_approval"] or 0,
            "approved": invoice_data["approved"] or 0,
            "rejected": invoice_data["rejected"] or 0
        }


if __name__ == "__main__":
    print("===== EXECUTIVE FINANCE DASHBOARD =====")

    metrics = get_dashboard_metrics()

    for name, value in metrics.items():
        print(f"{name.replace('_', ' ').title()}: {value}")

