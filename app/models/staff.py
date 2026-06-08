"""Staff / doctors registry and payroll model.

Tracks clinic personnel (doctors, nurses, reception, support) together
with how they are paid (fixed salary, commission on the treatments they
perform, or both), the commission they have earned from treatments, the
payouts recorded for them, and the remaining balance owed.
"""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db

PAY_TYPES = {
    "salary": "معاش ثابت",
    "commission": "فیصدی",
    "both": "معاش + فیصدی",
}
PAYMENT_KINDS = {
    "salary": "معاش",
    "commission": "فیصدی",
    "bonus": "پاداش",
}


# --------------------------------------------------------------------------
# CRUD
# --------------------------------------------------------------------------

def create(full_name: str, position: str, phone: str, pay_type: str,
           base_salary: float, commission_pct: float,
           is_provider: int = 0, notes: str = "") -> int:
    return db.insert(
        """INSERT INTO staff (full_name, position, phone, pay_type,
           base_salary, commission_pct, is_provider, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (full_name.strip(), position, phone.strip(), pay_type,
         base_salary, commission_pct, is_provider, notes),
    )


def update(staff_id: int, full_name: str, position: str, phone: str,
           pay_type: str, base_salary: float, commission_pct: float,
           is_provider: int, is_active: int, notes: str = "") -> None:
    db.execute(
        """UPDATE staff SET full_name = ?, position = ?, phone = ?,
           pay_type = ?, base_salary = ?, commission_pct = ?,
           is_provider = ?, is_active = ?, notes = ? WHERE id = ?""",
        (full_name.strip(), position, phone.strip(), pay_type, base_salary,
         commission_pct, is_provider, is_active, notes, staff_id),
    )


def delete(staff_id: int) -> None:
    db.execute("DELETE FROM staff WHERE id = ?", (staff_id,))


def get(staff_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM staff WHERE id = ?", (staff_id,))
    return dict(row) if row else None


def all_staff(active_only: bool = False) -> list[dict]:
    where = "WHERE is_active = 1" if active_only else ""
    rows = db.query_all(f"SELECT * FROM staff {where} ORDER BY full_name")
    return [dict(r) for r in rows]


def providers() -> list[dict]:
    """Active staff who can be selected as the provider of a visit."""
    rows = db.query_all(
        "SELECT * FROM staff WHERE is_active = 1 AND is_provider = 1 "
        "ORDER BY full_name"
    )
    return [dict(r) for r in rows]


def count() -> int:
    row = db.query_one("SELECT COUNT(*) AS c FROM staff")
    return row["c"] if row else 0


# --------------------------------------------------------------------------
# Earnings & payouts
# --------------------------------------------------------------------------

def treatments_total(staff_id: int) -> float:
    """Total value of treatments performed by this staff member."""
    row = db.query_one(
        "SELECT COALESCE(SUM(cost), 0) AS s FROM visits WHERE staff_id = ?",
        (staff_id,),
    )
    return float(row["s"]) if row else 0.0


def add_payment(staff_id: int, amount: float, kind: str = "salary",
                period: str = "", method: str = "cash",
                pay_date: Optional[str] = None, notes: str = "",
                created_by: Optional[int] = None) -> int:
    if not pay_date:
        pay_date = datetime.date.today().isoformat()
    pay_id = db.insert(
        """INSERT INTO staff_payments (staff_id, amount, kind, period,
           method, pay_date, notes, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (staff_id, amount, kind, period, method, pay_date, notes, created_by),
    )
    db.execute(
        "UPDATE staff_payments SET receipt_no = ? WHERE id = ?",
        (f"R-{pay_id:05d}", pay_id),
    )
    return pay_id


def delete_payment(payment_id: int) -> None:
    db.execute("DELETE FROM staff_payments WHERE id = ?", (payment_id,))


def get_payment(payment_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM staff_payments WHERE id = ?", (payment_id,))
    return dict(row) if row else None


def payments(staff_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM staff_payments WHERE staff_id = ? "
        "ORDER BY pay_date DESC, id DESC",
        (staff_id,),
    )
    return [dict(r) for r in rows]


def _sum_payments(staff_id: int, kind: Optional[str] = None) -> float:
    if kind:
        row = db.query_one(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
            "WHERE staff_id = ? AND kind = ?",
            (staff_id, kind),
        )
    else:
        row = db.query_one(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
            "WHERE staff_id = ?",
            (staff_id,),
        )
    return float(row["s"]) if row else 0.0


def summary(staff_id: int) -> dict:
    """Return a full payroll summary for a staff member."""
    s = get(staff_id) or {}
    pct = float(s.get("commission_pct") or 0)
    treat_total = treatments_total(staff_id)
    commission_earned = treat_total * pct / 100.0
    commission_paid = _sum_payments(staff_id, "commission")
    salary_paid = _sum_payments(staff_id, "salary")
    bonus_paid = _sum_payments(staff_id, "bonus")
    total_paid = _sum_payments(staff_id)
    return {
        "treatments_total": treat_total,
        "commission_earned": commission_earned,
        "commission_paid": commission_paid,
        "commission_balance": commission_earned - commission_paid,
        "salary_paid": salary_paid,
        "bonus_paid": bonus_paid,
        "total_paid": total_paid,
        "base_salary": float(s.get("base_salary") or 0),
    }


def total_paid_between(start_iso: str, end_iso: str) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
        "WHERE pay_date BETWEEN ? AND ?",
        (start_iso, end_iso),
    )
    return float(row["s"]) if row else 0.0
