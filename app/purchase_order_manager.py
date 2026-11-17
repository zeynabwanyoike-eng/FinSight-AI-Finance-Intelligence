
from decimal import Decimal, InvalidOperation
from database.invoice_database import get_connection


def initialize_purchase_order_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier TEXT NOT NULL,
                po_number TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'OPEN',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (po_id) REFERENCES purchase_orders(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_po_links (
                invoice_id INTEGER PRIMARY KEY,
                po_id INTEGER NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (po_id) REFERENCES purchase_orders(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS goods_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                grn_number TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'RECORDED',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (po_id) REFERENCES purchase_orders(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS goods_receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grn_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                FOREIGN KEY (grn_id) REFERENCES goods_receipts(id)
            )
        """)


def create_purchase_order(supplier, po_number):
    initialize_purchase_order_tables()

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO purchase_orders (supplier, po_number)
            VALUES (?, ?)
        """, (supplier.strip(), po_number.strip()))

        return cursor.lastrowid


def add_purchase_order_item(po_id, description, quantity, unit_price):
    quantity = Decimal(str(quantity))
    unit_price = Decimal(str(unit_price))

    if quantity <= 0 or unit_price <= 0:
        raise ValueError("Quantity and unit price must be greater than zero.")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO purchase_order_items
            (po_id, description, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        """, (po_id, description.strip(), float(quantity), float(unit_price)))


def add_invoice_item(invoice_id, description, quantity, unit_price):
    quantity = Decimal(str(quantity))
    unit_price = Decimal(str(unit_price))

    if quantity <= 0 or unit_price <= 0:
        raise ValueError("Quantity and unit price must be greater than zero.")

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO invoice_items
            (invoice_id, description, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, description.strip(), float(quantity), float(unit_price)))


def link_invoice_to_purchase_order(invoice_id, po_id):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO invoice_po_links (invoice_id, po_id)
            VALUES (?, ?)
            ON CONFLICT(invoice_id)
            DO UPDATE SET po_id = excluded.po_id
        """, (invoice_id, po_id))


def normalize_description(value):
    return " ".join(value.strip().casefold().split())


def to_decimal(value):
    return Decimal(str(value)).normalize()


def match_invoice_to_purchase_order(invoice_id):
    initialize_purchase_order_tables()

    with get_connection() as conn:
        link = conn.execute("""
            SELECT po_id FROM invoice_po_links
            WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()

        if link is None:
            return {
                "status": "REQUIRES_REVIEW",
                "message": "No purchase order linked to this invoice."
            }

        po_id = link["po_id"]

        invoice = conn.execute("""
            SELECT supplier FROM invoices WHERE id = ?
        """, (invoice_id,)).fetchone()

        purchase_order = conn.execute("""
            SELECT supplier, status FROM purchase_orders
            WHERE id = ?
        """, (po_id,)).fetchone()

        if invoice is None or purchase_order is None:
            return {
                "status": "REQUIRES_REVIEW",
                "message": "Invoice or purchase order not found."
            }

        if invoice["supplier"].strip().casefold() != purchase_order["supplier"].strip().casefold():
            return {
                "status": "MISMATCH",
                "message": "Supplier does not match."
            }

        if purchase_order["status"] != "OPEN":
            return {
                "status": "REQUIRES_REVIEW",
                "message": "Purchase order is not open."
            }

        ordered_items = conn.execute("""
            SELECT description, quantity, unit_price
            FROM purchase_order_items WHERE po_id = ?
        """, (po_id,)).fetchall()

        invoiced_items = conn.execute("""
            SELECT description, quantity, unit_price
            FROM invoice_items WHERE invoice_id = ?
        """, (invoice_id,)).fetchall()

        if not ordered_items or not invoiced_items:
            return {
                "status": "REQUIRES_REVIEW",
                "message": "Purchase order or invoice has no recorded line items."
            }

        discrepancies = []

        ordered = {}
        invoiced = {}

        for item in ordered_items:
            name = normalize_description(item["description"])
            if name in ordered:
                return {
                    "status": "REQUIRES_REVIEW",
                    "message": f"Duplicate purchase order item: {item['description']}"
                }
            ordered[name] = item

        for item in invoiced_items:
            name = normalize_description(item["description"])
            if name in invoiced:
                return {
                    "status": "REQUIRES_REVIEW",
                    "message": f"Duplicate invoice item: {item['description']}"
                }
            invoiced[name] = item

        for name, item in ordered.items():
            if name not in invoiced:
                discrepancies.append(f"Missing invoice item: {item['description']}")
                continue

            invoice_item = invoiced[name]

            try:
                if to_decimal(item["quantity"]) != to_decimal(invoice_item["quantity"]):
                    discrepancies.append(f"Quantity mismatch: {item['description']}")

                if to_decimal(item["unit_price"]) != to_decimal(invoice_item["unit_price"]):
                    discrepancies.append(f"Price mismatch: {item['description']}")
            except InvalidOperation:
                discrepancies.append(f"Invalid numeric value: {item['description']}")

        for name, item in invoiced.items():
            if name not in ordered:
                discrepancies.append(f"Unordered invoice item: {item['description']}")

        return {
            "status": "MATCHED" if not discrepancies else "MISMATCH",
            "purchase_order_id": po_id,
            "invoice_id": invoice_id,
            "discrepancies": discrepancies
        }


# GOODS RECEIVED NOTE MODULE

def create_goods_receipt(po_id, grn_number):
    initialize_purchase_order_tables()

    with get_connection() as conn:
        po = conn.execute("""
            SELECT id FROM purchase_orders WHERE id = ?
        """, (po_id,)).fetchone()

        if po is None:
            raise ValueError("Purchase order does not exist.")

        cursor = conn.execute("""
            INSERT INTO goods_receipts (po_id, grn_number)
            VALUES (?, ?)
        """, (po_id, grn_number.strip()))

        return cursor.lastrowid


def add_goods_receipt_item(grn_id, description, quantity):
    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError("Received quantity must be greater than zero.")

    with get_connection() as conn:
        grn = conn.execute("""
            SELECT id FROM goods_receipts WHERE id = ?
        """, (grn_id,)).fetchone()

        if grn is None:
            raise ValueError("Goods receipt does not exist.")

        conn.execute("""
            INSERT INTO goods_receipt_items
            (grn_id, description, quantity)
            VALUES (?, ?, ?)
        """, (grn_id, description.strip(), float(quantity)))


def match_invoice_to_goods_receipt(invoice_id, grn_id):
    initialize_purchase_order_tables()

    with get_connection() as conn:
        link = conn.execute("""
            SELECT po_id FROM invoice_po_links
            WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()

        grn = conn.execute("""
            SELECT po_id, status FROM goods_receipts
            WHERE id = ?
        """, (grn_id,)).fetchone()

        if link is None or grn is None:
            return {
                "status": "REQUIRES_REVIEW",
                "message": "Invoice link or goods receipt not found."
            }

        if link["po_id"] != grn["po_id"]:
            return {
                "status": "MISMATCH",
                "message": "Goods receipt belongs to a different purchase order."
            }

        if grn["status"] != "RECORDED":
            return {
                "status": "REQUIRES_REVIEW",
                "message": "Goods receipt is not available for matching."
            }

        invoice_items = conn.execute("""
            SELECT description, quantity
            FROM invoice_items WHERE invoice_id = ?
        """, (invoice_id,)).fetchall()

        received_items = conn.execute("""
            SELECT description, quantity
            FROM goods_receipt_items WHERE grn_id = ?
        """, (grn_id,)).fetchall()

        if not invoice_items or not received_items:
            return {
                "status": "REQUIRES_REVIEW",
                "message": "Invoice or goods receipt has no recorded items."
            }

        invoice_map = {}
        received_map = {}

        for item in invoice_items:
            name = normalize_description(item["description"])
            if name in invoice_map:
                return {
                    "status": "REQUIRES_REVIEW",
                    "message": f"Duplicate invoice item: {item['description']}"
                }
            invoice_map[name] = item

        for item in received_items:
            name = normalize_description(item["description"])
            if name in received_map:
                return {
                    "status": "REQUIRES_REVIEW",
                    "message": f"Duplicate received item: {item['description']}"
                }
            received_map[name] = item

        discrepancies = []

        for name, invoice_item in invoice_map.items():
            if name not in received_map:
                discrepancies.append(
                    f"Item not received: {invoice_item['description']}"
                )
                continue

            received_item = received_map[name]

            try:
                invoiced_quantity = to_decimal(invoice_item["quantity"])
                received_quantity = to_decimal(received_item["quantity"])

                if invoiced_quantity > received_quantity:
                    discrepancies.append(
                        f"Invoice quantity exceeds received quantity: {invoice_item['description']}"
                    )

            except InvalidOperation:
                discrepancies.append(
                    f"Invalid quantity: {invoice_item['description']}"
                )

        return {
            "status": "MATCHED" if not discrepancies else "MISMATCH",
            "invoice_id": invoice_id,
            "goods_receipt_id": grn_id,
            "discrepancies": discrepancies
        }


if __name__ == "__main__":
    initialize_purchase_order_tables()
    print("Purchase order and goods receipt tables initialized successfully.")
