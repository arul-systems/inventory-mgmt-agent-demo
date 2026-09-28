import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.environ.get("INVENTORY_DB_PATH", Path(__file__).parent / "inventory.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_email TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    reorder_threshold INTEGER NOT NULL DEFAULT 0,
    location TEXT,
    vendor_id INTEGER,
    FOREIGN KEY (vendor_id) REFERENCES vendors (id)
);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    from_location TEXT NOT NULL,
    to_location TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items (id)
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status TEXT NOT NULL DEFAULT 'ordered',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    received_at TEXT,
    FOREIGN KEY (item_id) REFERENCES items (id),
    FOREIGN KEY (vendor_id) REFERENCES vendors (id)
);
"""

SEED_VENDORS = [
    ("Acme Supplies", "sales@acmesupplies.com", "555-0100"),
    ("Global Parts Co.", "contact@globalparts.com", "555-0142"),
    ("Northwind Traders", "orders@northwind.com", "555-0199"),
]

SEED_ITEMS = [
    ("SKU-1001", "Widget A", 120, 25, "Warehouse-1", 1),
    ("SKU-1002", "Widget B", 40, 30, "Warehouse-1", 1),
    ("SKU-2001", "Gadget X", 15, 20, "Warehouse-2", 2),
    ("SKU-3001", "Bolt Pack", 500, 100, "Warehouse-2", 3),
]

SEED_TRANSFERS = [
    (1, "Warehouse-1", "Warehouse-2", 10, "completed"),
]


def get_connection() -> sqlite3.Connection:
    """Return a new connection to the inventory sqlite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def schema_exists() -> bool:
    """Return True if every table defined in SCHEMA is already present."""
    expected = set(re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", SCHEMA))
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return expected <= {row["name"] for row in rows}


def init_db() -> None:
    """Create the database schema, skipping it if all tables already exist."""
    if schema_exists():
        return
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def seed_db() -> None:
    """Populate the database with sample data (no-op if already seeded)."""
    with get_connection() as conn:
        if conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]:
            return
        conn.executemany(
            "INSERT INTO vendors (name, contact_email, phone) VALUES (?, ?, ?)",
            SEED_VENDORS,
        )
        conn.executemany(
            """INSERT INTO items (sku, name, quantity, reorder_threshold, location, vendor_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            SEED_ITEMS,
        )
        conn.executemany(
            """INSERT INTO transfers (item_id, from_location, to_location, quantity, status)
               VALUES (?, ?, ?, ?, ?)""",
            SEED_TRANSFERS,
        )
        conn.commit()


def create_item(
    sku: str,
    name: str,
    quantity: int,
    reorder_threshold: int,
    location: Optional[str] = None,
    vendor_id: Optional[int] = None,
) -> dict:
    """Insert a new item and return the created row."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO items (sku, name, quantity, reorder_threshold, location, vendor_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sku, name, quantity, reorder_threshold, location, vendor_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM items WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def get_item(sku: str) -> Optional[dict]:
    """Fetch a single item by SKU. Returns None if it doesn't exist."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
        return dict(row) if row else None


def update_item(
    sku: str,
    name: Optional[str] = None,
    quantity: Optional[int] = None,
    reorder_threshold: Optional[int] = None,
    location: Optional[str] = None,
    vendor_id: Optional[int] = None,
) -> Optional[dict]:
    """Update the given fields (ignoring unset ones) for the item with this SKU.

    Returns the updated row, or None if no item with this SKU exists.
    """
    updates = {
        "name": name,
        "quantity": quantity,
        "reorder_threshold": reorder_threshold,
        "location": location,
        "vendor_id": vendor_id,
    }
    updates = {k: v for k, v in updates.items() if v is not None}

    with get_connection() as conn:
        if updates:
            set_clause = ", ".join(f"{column} = ?" for column in updates)
            conn.execute(
                f"UPDATE items SET {set_clause} WHERE sku = ?",
                (*updates.values(), sku),
            )
            conn.commit()
        row = conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
        return dict(row) if row else None


def delete_item(sku: str) -> bool:
    """Delete the item with this SKU. Returns True if a row was deleted."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM items WHERE sku = ?", (sku,))
        conn.commit()
        return cursor.rowcount > 0


def list_locations() -> list[str]:
    """Return every known warehouse/location, alphabetically."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT location FROM items WHERE location IS NOT NULL
               UNION SELECT to_location FROM transfers
               UNION SELECT from_location FROM transfers
               ORDER BY 1"""
        ).fetchall()
        return [row[0] for row in rows]


def transfer_item(sku: str, to_location: str) -> dict:
    """Move the whole item to another location and record the transfer.

    Returns {"item": <updated item row>, "transfer": <transfer row>}.
    Raises ValueError if the SKU doesn't exist or the item is already at the destination.
    """
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        item = conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
        if item is None:
            raise ValueError(f"No item found with sku '{sku}'.")
        if item["location"] == to_location:
            raise ValueError(f"Item '{sku}' is already at '{to_location}'.")

        conn.execute("UPDATE items SET location = ? WHERE id = ?", (to_location, item["id"]))
        cursor = conn.execute(
            """INSERT INTO transfers (item_id, from_location, to_location, quantity, status)
               VALUES (?, ?, ?, ?, 'completed')""",
            (item["id"], item["location"], to_location, item["quantity"]),
        )
        conn.commit()
        return {
            "item": dict(conn.execute("SELECT * FROM items WHERE id = ?", (item["id"],)).fetchone()),
            "transfer": dict(
                conn.execute("SELECT * FROM transfers WHERE id = ?", (cursor.lastrowid,)).fetchone()
            ),
        }


_PO_SELECT = """SELECT po.*, i.sku, v.name AS vendor_name
                FROM purchase_orders po
                JOIN items i ON i.id = po.item_id
                JOIN vendors v ON v.id = po.vendor_id"""


def create_purchase_order(sku: str, quantity: int) -> dict:
    """Cut a purchase order for an item with the item's assigned vendor.

    Returns {"item": <item row>, "purchase_order": <purchase order row>}.
    Raises ValueError if the quantity isn't positive, the SKU doesn't exist, or the item has no vendor.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    with get_connection() as conn:
        item = conn.execute("SELECT * FROM items WHERE sku = ?", (sku,)).fetchone()
        if item is None:
            raise ValueError(f"No item found with sku '{sku}'.")
        if item["vendor_id"] is None:
            raise ValueError(f"Item '{sku}' has no vendor assigned, so a purchase order can't be created.")
        cursor = conn.execute(
            "INSERT INTO purchase_orders (item_id, vendor_id, quantity) VALUES (?, ?, ?)",
            (item["id"], item["vendor_id"], quantity),
        )
        conn.commit()
        po = conn.execute(f"{_PO_SELECT} WHERE po.id = ?", (cursor.lastrowid,)).fetchone()
        return {"item": dict(item), "purchase_order": dict(po)}


def receive_purchase_order(po_id: int) -> dict:
    """Mark a purchase order as received and add its quantity to the item's stock.

    Returns {"item": <updated item row>, "purchase_order": <purchase order row>}.
    Raises ValueError if the purchase order doesn't exist or was already received.
    """
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        po = conn.execute("SELECT * FROM purchase_orders WHERE id = ?", (po_id,)).fetchone()
        if po is None:
            raise ValueError(f"No purchase order found with id {po_id}.")
        if po["status"] != "ordered":
            raise ValueError(f"Purchase order {po_id} has already been received.")

        conn.execute(
            "UPDATE purchase_orders SET status = 'received', received_at = CURRENT_TIMESTAMP WHERE id = ?",
            (po_id,),
        )
        conn.execute(
            "UPDATE items SET quantity = quantity + ? WHERE id = ?",
            (po["quantity"], po["item_id"]),
        )
        conn.commit()
        return {
            "item": dict(conn.execute("SELECT * FROM items WHERE id = ?", (po["item_id"],)).fetchone()),
            "purchase_order": dict(conn.execute(f"{_PO_SELECT} WHERE po.id = ?", (po_id,)).fetchone()),
        }


def list_purchase_orders(sku: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    """List purchase orders, optionally filtered by item SKU and/or status ('ordered' or 'received')."""
    clauses, params = [], []
    if sku is not None:
        clauses.append("i.sku = ?")
        params.append(sku)
    if status is not None:
        clauses.append("po.status = ?")
        params.append(status)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(f"{_PO_SELECT}{where} ORDER BY po.id", params).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    init_db()
    seed_db()
