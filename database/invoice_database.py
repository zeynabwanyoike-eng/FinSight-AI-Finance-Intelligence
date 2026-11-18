
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "finance.db"


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier TEXT NOT NULL,
                invoice_number TEXT NOT NULL,
                invoice_date TEXT,
                total REAL,
                processing_status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(supplier, invoice_number)
            )
        """)


def save_invoice(invoice, status):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO invoices (
                supplier,
                invoice_number,
                invoice_date,
                total,
                processing_status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            invoice["supplier"],
            invoice["invoice_number"],
            invoice["invoice_date"],
            invoice["total"],
            status
        ))

        return cursor.lastrowid


def get_all_invoices():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM invoices ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


if __name__ == "__main__":
    initialize_database()
    print("Finance database initialized successfully.")
    print("Database location:", DATABASE_PATH)
