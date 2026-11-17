
import unittest
from decimal import Decimal

from src.validation.invoice_validator import validate_invoice
from src.validation.duplicate_detector import check_duplicate
from database.invoice_database import get_all_invoices
from app.payment_manager import get_payment_summary
from app.purchase_order_manager import (
    match_invoice_to_purchase_order,
    match_invoice_to_goods_receipt
)
from app.anomaly_detector import detect_invoice_anomalies
from app.finance_assistant import (
    get_financial_summary,
    get_supplier_balances,
    answer_question
)


class TestFinanceSystem(unittest.TestCase):

    def test_invoice_validation(self):
        invoice = {
            "invoice_number": "TEST-001",
            "invoice_date": "15/11/2026",
            "total": "15000"
        }

        result = validate_invoice(invoice)
        self.assertTrue(result["valid"])

    def test_duplicate_detection(self):
        invoice = {
            "supplier": "ABC Supplies",
            "invoice_number": "INV-2026-001"
        }

        existing_invoices = [
            {
                "supplier": "ABC Supplies",
                "invoice_number": "INV-2026-001"
            }
        ]

        result = check_duplicate(invoice, existing_invoices)

        self.assertEqual(
            result["status"],
            "DUPLICATE_FLAGGED"
        )
        self.assertTrue(result["duplicate"])

    def test_payment_summary(self):
        result = get_payment_summary(2)

        self.assertEqual(
            Decimal(str(result["outstanding_balance"])),
            Decimal("0")
        )
        self.assertEqual(result["payment_status"], "PAID")

    def test_purchase_order_matching(self):
        result = match_invoice_to_purchase_order(2)
        self.assertEqual(result["status"], "MATCHED")

    def test_goods_receipt_matching(self):
        from database.invoice_database import get_connection

        with get_connection() as conn:
            grn = conn.execute("""
                SELECT id FROM goods_receipts
                WHERE po_id = 1
                ORDER BY id DESC LIMIT 1
            """).fetchone()

        self.assertIsNotNone(grn)

        result = match_invoice_to_goods_receipt(
            2,
            grn["id"]
        )

        self.assertEqual(result["status"], "MATCHED")

    def test_anomaly_detection(self):
        results = detect_invoice_anomalies(20000)

        self.assertTrue(
            any(
                item["type"] == "HIGH_VALUE"
                and item["invoice_id"] == 1
                for item in results
            )
        )

    def test_financial_summary(self):
        invoices = get_all_invoices()
        expected_invoice_count = len(invoices)

        expected_supplier_count = len({
            invoice["supplier"]
            for invoice in invoices
            if invoice["supplier"]
        })

        result = get_financial_summary()

        self.assertEqual(
            result["invoice_count"],
            expected_invoice_count
        )

        self.assertEqual(
            result["supplier_count"],
            expected_supplier_count
        )

    def test_supplier_analytics(self):
        invoices = get_all_invoices()

        expected_supplier_count = len({
            invoice["supplier"]
            for invoice in invoices
            if invoice["supplier"]
        })

        results = get_supplier_balances()

        self.assertEqual(
            len(results),
            expected_supplier_count
        )

    def test_finance_assistant(self):
        result = answer_question(
            "What is our total outstanding balance?"
        )

        self.assertIn("KES", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
