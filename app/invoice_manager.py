
from database.invoice_database import get_connection


def get_all_invoices():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM invoices ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def search_invoices(search_term):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM invoices
            WHERE supplier LIKE ? OR invoice_number LIKE ?
            ORDER BY id DESC
        """, (f"%{search_term}%", f"%{search_term}%")).fetchall()

        return [dict(row) for row in rows]


def filter_invoices(status):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM invoices
            WHERE processing_status = ?
            ORDER BY id DESC
        """, (status,)).fetchall()

        return [dict(row) for row in rows]


def get_financial_summary():
    with get_connection() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS invoice_count,
                COALESCE(SUM(total), 0) AS total_value,
                SUM(CASE WHEN processing_status = 'READY_FOR_APPROVAL'
                    THEN 1 ELSE 0 END) AS pending_approval,
                SUM(CASE WHEN processing_status = 'DUPLICATE_FLAGGED'
                    THEN 1 ELSE 0 END) AS duplicate_count
            FROM invoices
        """).fetchone()

        return dict(row)


if __name__ == "__main__":
    print("\n===== INVOICE REGISTER =====")
    for invoice in get_all_invoices():
        print(invoice)

    print("\n===== FINANCIAL SUMMARY =====")
    print(get_financial_summary())

    print("\n===== SEARCH RESULTS =====")
    print(search_invoices("ABC"))
