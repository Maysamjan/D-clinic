"""Clinic expense model + profit/loss helpers."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db

CATEGORIES = {
    "rent": "کرایه",
    "utilities": "برق / آب / انترنت",
    "supplies": "خرید مواد و تجهیزات",
    "salary": "معاش و تنخواه",
    "maintenance": "ترمیم و نگهداری",
    "marketing": "تبلیغات",
    "other": "متفرقه",
}


def create(category: str, description: str, amount: float,
           expense_date: Optional[str] = None, paid_to: str = "",
           created_by: Optional[int] = None) -> int:
    if not expense_date:
        expense_date = datetime.date.today().isoformat()
    return db.insert(
        """INSERT INTO expenses (category, description, amount, expense_date,
           paid_to, created_by) VALUES (?, ?, ?, ?, ?, ?)""",
        (category, description.strip(), amount, expense_date, paid_to, created_by),
    )


def update(expense_id: int, category: str, description: str, amount: float,
           expense_date: str, paid_to: str) -> None:
    db.execute(
        """UPDATE expenses SET category = ?, description = ?, amount = ?,
           expense_date = ?, paid_to = ? WHERE id = ?""",
        (category, description.strip(), amount, expense_date, paid_to, expense_id),
    )


def delete(expense_id: int) -> None:
    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def get(expense_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    return dict(row) if row else None


def between(start_iso: str, end_iso: str) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM expenses WHERE expense_date BETWEEN ? AND ? "
        "ORDER BY expense_date DESC, id DESC",
        (start_iso, end_iso),
    )
    return [dict(r) for r in rows]


def total_between(start_iso: str, end_iso: str) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM expenses "
        "WHERE expense_date BETWEEN ? AND ?",
        (start_iso, end_iso),
    )
    return float(row["s"]) if row else 0.0


def profit_loss(start_iso: str, end_iso: str) -> dict:
    """Income (patient payments) minus expenses and staff payments."""
    inc = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM payments "
        "WHERE pay_date BETWEEN ? AND ?", (start_iso, end_iso))
    staff = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
        "WHERE pay_date BETWEEN ? AND ?", (start_iso, end_iso))
    income = float(inc["s"]) if inc else 0.0
    staff_paid = float(staff["s"]) if staff else 0.0
    expenses = total_between(start_iso, end_iso)
    return {
        "income": income,
        "expenses": expenses,
        "staff_paid": staff_paid,
        "total_out": expenses + staff_paid,
        "net": income - expenses - staff_paid,
    }
