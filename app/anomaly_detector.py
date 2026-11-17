
from decimal import Decimal
from database.invoice_database import get_connection


DEFAULT_HIGH_VALUE_THRESHOLD = Decimal("100000")


def initialize_anomaly_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                UNIQUE(invoice_id, anomaly_type)
            )
        """)


def save_anomaly(invoice_id, anomaly_type, severity, description):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO invoice_anomalies
            (invoice_id, anomaly_type, severity, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(invoice_id, anomaly_type)
            DO UPDATE SET
                severity = excluded.severity,
                description = excluded.description,
                detected_at = CURRENT_TIMESTAMP
        """, (invoice_id, anomaly_type, severity, description))


def detect_invoice_anomalies(
    high_value_threshold=DEFAULT_HIGH_VALUE_THRESHOLD
):
    initialize_anomaly_table()

    high_value_threshold = Decimal(str(high_value_threshold))
    findings = []

    with get_connection() as conn:
        invoices = conn.execute("""
            SELECT id, supplier, invoice_number, total, created_at
            FROM invoices
            ORDER BY id
        """).fetchall()

        for invoice in invoices:
            invoice_id = invoice["id"]
            supplier = invoice["supplier"]
            amount = Decimal(str(invoice["total"]))

            # Rule 1: High-value invoice
            if amount >= high_value_threshold:
                description = (
                    f"Invoice value {amount} meets or exceeds "
                    f"the high-value threshold of {high_value_threshold}."
                )

                findings.append({
                    "invoice_id": invoice_id,
                    "type": "HIGH_VALUE",
                    "severity": "HIGH",
                    "description": description
                })

            # Rule 2: Repeated invoice amounts from the same supplier
            repeated = conn.execute("""
                SELECT COUNT(*) AS total
                FROM invoices
                WHERE supplier = ?
                  AND total = ?
                  AND id != ?
            """, (supplier, float(amount), invoice_id)).fetchone()

            if repeated["total"] > 0:
                description = (
                    f"Another invoice from {supplier} has the same "
                    f"invoice amount of {amount}."
                )

                findings.append({
                    "invoice_id": invoice_id,
                    "type": "REPEATED_AMOUNT",
                    "severity": "MEDIUM",
                    "description": description
                })

            # Rule 3: Unusually large compared with supplier history
            history = conn.execute("""
                SELECT total
                FROM invoices
                WHERE supplier = ?
                  AND id < ?
            """, (supplier, invoice_id)).fetchall()

            if len(history) >= 3:
                historical_amounts = [
                    Decimal(str(row["total"]))
                    for row in history
                ]

                average = sum(
                    historical_amounts, Decimal("0")
                ) / Decimal(len(historical_amounts))

                if average > 0 and amount >= average * Decimal("3"):
                    description = (
                        f"Invoice amount {amount} is at least three "
                        f"times the supplier's historical average "
                        f"of {average.quantize(Decimal('0.01'))}."
                    )

                    findings.append({
                        "invoice_id": invoice_id,
                        "type": "UNUSUAL_SUPPLIER_AMOUNT",
                        "severity": "HIGH",
                        "description": description
                    })

    # Save findings after reading the invoice records
    for finding in findings:
        save_anomaly(
            finding["invoice_id"],
            finding["type"],
            finding["severity"],
            finding["description"]
        )

    return findings


def get_all_anomalies():
    initialize_anomaly_table()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                a.id,
                a.invoice_id,
                i.supplier,
                i.invoice_number,
                i.total,
                a.anomaly_type,
                a.severity,
                a.description,
                a.detected_at
            FROM invoice_anomalies a
            JOIN invoices i ON i.id = a.invoice_id
            ORDER BY a.detected_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


if __name__ == "__main__":
    results = detect_invoice_anomalies()

    print("===== INVOICE ANOMALY DETECTION =====")

    if not results:
        print("No anomalies detected using the current rules.")

    for finding in results:
        print(finding)

    print("\n===== SAVED ANOMALY RECORDS =====")

    for anomaly in get_all_anomalies():
        print(anomaly)
