"""Inventory / store-room model.

Tracks medicines, equipment and consumables held in the clinic store,
with stock-in / stock-out movements, low-stock detection and expiry
warnings for medicines.
"""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db

CATEGORIES = {
    "medicine": "دوا",
    "equipment": "تجهیزات",
    "consumable": "مواد مصرفی",
}

REASONS = {
    "purchase": "خرید / ورود",
    "use": "مصرف / خروج",
    "adjust": "تصحیح موجودی",
    "expire": "ضایعات / انقضا",
}


# --------------------------------------------------------------------------
# CRUD
# --------------------------------------------------------------------------

def create(name: str, category: str, unit: str, quantity: float,
           min_quantity: float, unit_price: float, supplier: str = "",
           expiry_date: Optional[str] = None, notes: str = "") -> int:
    item_id = db.insert(
        """INSERT INTO inventory_items (name, category, unit, quantity,
           min_quantity, unit_price, supplier, expiry_date, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name.strip(), category, unit, quantity, min_quantity, unit_price,
         supplier, expiry_date, notes),
    )
    if quantity:
        db.execute(
            """INSERT INTO inventory_movements (item_id, change, reason, note)
               VALUES (?, ?, 'purchase', 'موجودی اولیه')""",
            (item_id, quantity),
        )
    return item_id


def update(item_id: int, name: str, category: str, unit: str,
           min_quantity: float, unit_price: float, supplier: str,
           expiry_date: Optional[str], notes: str, is_active: int = 1) -> None:
    """Update item details (quantity is changed only via stock movements)."""
    db.execute(
        """UPDATE inventory_items SET name = ?, category = ?, unit = ?,
           min_quantity = ?, unit_price = ?, supplier = ?, expiry_date = ?,
           notes = ?, is_active = ? WHERE id = ?""",
        (name.strip(), category, unit, min_quantity, unit_price, supplier,
         expiry_date, notes, is_active, item_id),
    )


def delete(item_id: int) -> None:
    db.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))


def get(item_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM inventory_items WHERE id = ?", (item_id,))
    return dict(row) if row else None


def all_items(category: Optional[str] = None, search: str = "",
              active_only: bool = False) -> list[dict]:
    clauses = []
    params: list = []
    if active_only:
        clauses.append("is_active = 1")
    if category:
        clauses.append("category = ?")
        params.append(category)
    if search.strip():
        clauses.append("(name LIKE ? OR supplier LIKE ?)")
        params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = db.query_all(
        f"SELECT * FROM inventory_items {where} ORDER BY name", params)
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# Stock movements
# --------------------------------------------------------------------------

def adjust_stock(item_id: int, change: float, reason: str = "purchase",
                 note: str = "", movement_date: Optional[str] = None,
                 created_by: Optional[int] = None) -> None:
    """Record a stock movement and update the on-hand quantity."""
    if not movement_date:
        movement_date = datetime.date.today().isoformat()
    db.execute(
        """INSERT INTO inventory_movements (item_id, change, reason, note,
           movement_date, created_by) VALUES (?, ?, ?, ?, ?, ?)""",
        (item_id, change, reason, note, movement_date, created_by),
    )
    db.execute(
        "UPDATE inventory_items SET quantity = quantity + ? WHERE id = ?",
        (change, item_id),
    )


def movements(item_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM inventory_movements WHERE item_id = ? "
        "ORDER BY movement_date DESC, id DESC",
        (item_id,),
    )
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# Alerts & aggregates
# --------------------------------------------------------------------------

def low_stock() -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM inventory_items WHERE is_active = 1 "
        "AND min_quantity > 0 AND quantity <= min_quantity ORDER BY name")
    return [dict(r) for r in rows]


def expiring_soon(days: int = 60) -> list[dict]:
    today = datetime.date.today()
    limit = (today + datetime.timedelta(days=days)).isoformat()
    rows = db.query_all(
        """SELECT * FROM inventory_items WHERE is_active = 1
           AND expiry_date IS NOT NULL AND expiry_date != ''
           AND expiry_date <= ? ORDER BY expiry_date""",
        (limit,),
    )
    return [dict(r) for r in rows]


def total_value() -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(quantity * unit_price), 0) AS s "
        "FROM inventory_items WHERE is_active = 1")
    return float(row["s"]) if row else 0.0


def count() -> int:
    row = db.query_one("SELECT COUNT(*) AS c FROM inventory_items")
    return row["c"] if row else 0
