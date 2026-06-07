"""Payment model (supports partial payments)."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db


def create(patient_id: int, amount: float, method: str = "cash",
           pay_date: Optional[str] = None, notes: str = "",
           visit_id: Optional[int] = None,
           created_by: Optional[int] = None) -> int:
    if not pay_date:
        pay_date = datetime.date.today().isoformat()
    return db.insert(
        """INSERT INTO payments (patient_id, visit_id, amount, method,
           pay_date, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, visit_id, amount, method, pay_date, notes, created_by),
    )


def delete(payment_id: int) -> None:
    db.execute("DELETE FROM payments WHERE id = ?", (payment_id,))


def for_patient(patient_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM payments WHERE patient_id = ? ORDER BY pay_date DESC, id DESC",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def total_on(date_iso: str) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM payments WHERE pay_date = ?",
        (date_iso,),
    )
    return float(row["s"]) if row else 0.0


def total_between(start_iso: str, end_iso: str) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM payments "
        "WHERE pay_date BETWEEN ? AND ?",
        (start_iso, end_iso),
    )
    return float(row["s"]) if row else 0.0
