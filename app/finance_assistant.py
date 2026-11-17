
from decimal import Decimal
from database.invoice_database import get_connection


def get_financial_summary():
    with get_connection() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS invoice_count,
                COUNT(DISTINCT supplier) AS supplier_count,
                COALESCE(SUM(total), 0) AS total_invoiced
            FROM invoices
        """).fetchone()

        paid = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total_paid
            FROM invoice_payments
        """).fetchone()

        return {
            "invoice_count": row["invoice_count"],
            "supplier_count": row["supplier_count"],
            "total_invoiced": Decimal(str(row["total_invoiced"])),
            "total_paid": Decimal(str(paid["total_paid"])),
            "outstanding": (
                Decimal(str(row["total_invoiced"]))
                - Decimal(str(paid["total_paid"]))
            )
        }


def get_supplier_balances():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                i.supplier,
                SUM(i.total) AS invoiced,
                SUM(COALESCE(p.paid, 0)) AS paid
            FROM invoices i
            LEFT JOIN (
                SELECT invoice_id, SUM(amount) AS paid
                FROM invoice_payments
                GROUP BY invoice_id
            ) p ON p.invoice_id = i.id
            GROUP BY i.supplier
            ORDER BY (SUM(i.total) - SUM(COALESCE(p.paid, 0))) DESC
        """).fetchall()

        return [
            {
                "supplier": row["supplier"],
                "invoiced": Decimal(str(row["invoiced"])),
                "paid": Decimal(str(row["paid"])),
                "outstanding": (
                    Decimal(str(row["invoiced"]))
                    - Decimal(str(row["paid"]))
                )
            }
            for row in rows
        ]


def get_pending_invoices():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, supplier, invoice_number, total, processing_status
            FROM invoices
            WHERE processing_status IN (
                'READY_FOR_APPROVAL',
                'REQUIRES_REVIEW',
                'DUPLICATE_FLAGGED'
            )
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_anomalies():
    with get_connection() as conn:
        try:
            rows = conn.execute("""
                SELECT
                    invoice_id,
                    anomaly_type,
                    severity,
                    description
                FROM invoice_anomalies
                ORDER BY detected_at DESC
            """).fetchall()

            return [dict(row) for row in rows]

        except Exception:
            return []


def get_invoice_count_by_status():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT processing_status, COUNT(*) AS total
            FROM invoices
            GROUP BY processing_status
        """).fetchall()

        return {
            row["processing_status"]: row["total"]
            for row in rows
        }


def answer_question(question):
    question = question.strip().casefold()

    if not question:
        return "Please enter a finance question."

    # Outstanding balances
    if any(word in question for word in [
        "outstanding", "unpaid", "liability", "owe"
    ]):
        if "supplier" in question:
            balances = get_supplier_balances()

            if not balances:
                return "There are no supplier records."

            return "\n".join(
                f"{item['supplier']}: KES {item['outstanding']:,.2f} outstanding"
                for item in balances
            )

        summary = get_financial_summary()

        return (
            f"Total outstanding balance: "
            f"KES {summary['outstanding']:,.2f}"
        )

    # Payment information
    if any(word in question for word in [
        "paid", "payment", "payments"
    ]):
        summary = get_financial_summary()

        return (
            f"Total payments recorded: "
            f"KES {summary['total_paid']:,.2f}"
        )

    # Supplier information
    if "supplier" in question and any(word in question for word in [
        "highest", "top", "spending", "spent", "rank"
    ]):
        balances = get_supplier_balances()

        balances.sort(
            key=lambda item: item["invoiced"],
            reverse=True
        )

        if not balances:
            return "No supplier records found."

        return "\n".join(
            f"{item['supplier']}: KES {item['invoiced']:,.2f} invoiced"
            for item in balances
        )

    # Anomaly information
    if any(word in question for word in [
        "anomal", "suspicious", "flagged", "risk"
    ]):
        anomalies = get_anomalies()

        if not anomalies:
            return "No saved anomalies were found."

        return "\n".join(
            f"Invoice {item['invoice_id']} | "
            f"{item['severity']} | {item['anomaly_type']}: "
            f"{item['description']}"
            for item in anomalies
        )

    # Pending invoices and reviews
    if any(word in question for word in [
        "pending", "review", "approval", "approve"
    ]):
        invoices = get_pending_invoices()

        if not invoices:
            return "There are no invoices awaiting approval or review."

        return "\n".join(
            f"Invoice {item['invoice_number']} | "
            f"{item['supplier']} | KES {item['total']:,.2f} | "
            f"{item['processing_status']}"
            for item in invoices
        )

    # Invoice and supplier counts
    if any(word in question for word in [
        "how many", "count", "number of"
    ]):
        summary = get_financial_summary()

        return (
            f"Total invoices: {summary['invoice_count']}\n"
            f"Total suppliers: {summary['supplier_count']}"
        )

    # Overall financial summary
    if any(word in question for word in [
        "summary", "financial position", "total invoiced",
        "finance overview", "overview"
    ]):
        summary = get_financial_summary()

        return (
            f"FINANCIAL SUMMARY\n"
            f"Total invoices: {summary['invoice_count']}\n"
            f"Total suppliers: {summary['supplier_count']}\n"
            f"Total invoiced: KES {summary['total_invoiced']:,.2f}\n"
            f"Total paid: KES {summary['total_paid']:,.2f}\n"
            f"Outstanding: KES {summary['outstanding']:,.2f}"
        )

    return (
        "I couldn't identify that question yet.\n"
        "Try asking about outstanding balances, payments, "
        "suppliers, invoices, approvals, anomalies or financial summary."
    )


if __name__ == "__main__":
    print("===== AI FINANCE ASSISTANT =====")

    while True:
        question = input("\nAsk a finance question (or type exit): ")

        if question.strip().casefold() == "exit":
            print("Finance assistant closed.")
            break

        print("\n" + answer_question(question))
