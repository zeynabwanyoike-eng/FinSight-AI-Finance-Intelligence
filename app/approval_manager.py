
from database.invoice_database import get_connection


def create_audit_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS approval_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                performed_by TEXT NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def approve_invoice(invoice_id, approved_by):
    create_audit_table()

    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE invoices
            SET processing_status = 'APPROVED'
            WHERE id = ?
            AND processing_status = 'READY_FOR_APPROVAL'
        """, (invoice_id,))

        if cursor.rowcount == 1:
            conn.execute("""
                INSERT INTO approval_audit
                (invoice_id, action, performed_by)
                VALUES (?, 'APPROVED', ?)
            """, (invoice_id, approved_by))

            return {"success": True, "message": "Invoice approved and logged."}

        return {"success": False, "message": "Invoice not found or not eligible."}


def reject_invoice(invoice_id, rejected_by, reason):
    create_audit_table()

    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE invoices
            SET processing_status = 'REJECTED'
            WHERE id = ?
            AND processing_status = 'READY_FOR_APPROVAL'
        """, (invoice_id,))

        if cursor.rowcount == 1:
            conn.execute("""
                INSERT INTO approval_audit
                (invoice_id, action, performed_by, reason)
                VALUES (?, 'REJECTED', ?, ?)
            """, (invoice_id, rejected_by, reason))

            return {"success": True, "message": "Invoice rejected and logged."}

        return {"success": False, "message": "Invoice not found or not eligible."}


def get_approval_history():
    create_audit_table()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM approval_audit
            ORDER BY created_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


if __name__ == "__main__":
    print(approve_invoice(2, "Finance Manager"))
    print("APPROVAL HISTORY:")
    print(get_approval_history())
