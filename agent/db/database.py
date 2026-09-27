import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "inventory.db"

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


def init_db() -> None:
    """Create the database schema if it doesn't already exist."""
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


if __name__ == "__main__":
    init_db()
    seed_db()
