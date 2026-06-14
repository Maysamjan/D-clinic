"""Invoice model with line items."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db


def _make_number(invoice_id: int) -> str:
    year = datetime.date.today().year
    return f"INV-{year}-{invoice_id:05d}"


def create(patient_id: int, items: list[tuple[str, float]], paid: float = 0,
           issue_date: Optional[str] = None, notes: str = "",
           created_by: Optional[int] = None) -> int:
    """Create an invoice with *items* = list of (description, amount)."""
    if not issue_date:
        issue_date = datetime.date.today().isoformat()
    total = sum(float(a) for _, a in items)
    inv_id = db.insert(
        """INSERT INTO invoices (patient_id, total, paid, issue_date, notes,
           created_by) VALUES (?, ?, ?, ?, ?, ?)""",
        (patient_id, total, paid, issue_date, notes, created_by),
    )
    number = _make_number(inv_id)
    db.execute("UPDATE invoices SET number = ? WHERE id = ?", (number, inv_id))
    for desc, amount in items:
        db.execute(
            "INSERT INTO invoice_items (invoice_id, description, amount) "
            "VALUES (?, ?, ?)",
            (inv_id, desc, float(amount)),
        )
    return inv_id


def get(invoice_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    return dict(row) if row else None


def items(invoice_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id",
        (invoice_id,),
    )
    return [dict(r) for r in rows]


def for_patient(patient_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM invoices WHERE patient_id = ? ORDER BY id DESC",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def delete(invoice_id: int) -> None:
    db.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
