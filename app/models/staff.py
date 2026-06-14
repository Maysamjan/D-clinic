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

def next_suggested_code() -> str:
    """Suggest the next short numeric id (highest existing number + 1)."""
    rows = db.query_all("SELECT code FROM staff WHERE code IS NOT NULL")
    nums = []
    for r in rows:
        digits = "".join(ch for ch in (r["code"] or "") if ch.isdigit())
        if digits:
            nums.append(int(digits))
    return str((max(nums) + 1) if nums else 1)


def code_exists(code: str, exclude_id: int | None = None) -> bool:
    code = (code or "").strip()
    if not code:
        return False
    if exclude_id:
        row = db.query_one(
            "SELECT id FROM staff WHERE code = ? AND id != ?", (code, exclude_id))
    else:
        row = db.query_one("SELECT id FROM staff WHERE code = ?", (code,))
    return row is not None


def create(full_name: str, position: str, phone: str, pay_type: str,
           base_salary: float, commission_pct: float, is_provider: int = 0,
           notes: str = "", code: str = "") -> int:
    sid = db.insert(
        """INSERT INTO staff (full_name, position, phone, pay_type,
           base_salary, commission_pct, is_provider, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (full_name.strip(), position, phone.strip(), pay_type,
         base_salary, commission_pct, is_provider, notes),
    )
    code = (code or "").strip() or str(sid)
    db.execute("UPDATE staff SET code = ? WHERE id = ?", (code, sid))
    return sid


def update(staff_id: int, full_name: str, position: str, phone: str,
           pay_type: str, base_salary: float, commission_pct: float,
           is_provider: int, is_active: int, notes: str = "",
           code: str | None = None) -> None:
    db.execute(
        """UPDATE staff SET full_name = ?, position = ?, phone = ?,
           pay_type = ?, base_salary = ?, commission_pct = ?,
           is_provider = ?, is_active = ?, notes = ? WHERE id = ?""",
        (full_name.strip(), position, phone.strip(), pay_type, base_salary,
         commission_pct, is_provider, is_active, notes, staff_id),
    )
    if code is not None and code.strip():
        db.execute("UPDATE staff SET code = ? WHERE id = ?",
                   (code.strip(), staff_id))


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


def search(term: str = "", active_only: bool = True) -> list[dict]:
    """Search staff by name, code or position."""
    clauses = []
    params: list = []
    if active_only:
        clauses.append("is_active = 1")
    term = (term or "").strip()
    if term:
        like = f"%{term}%"
        clauses.append("(full_name LIKE ? OR code LIKE ? OR position LIKE ?)")
        params.extend([like, like, like])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = db.query_all(f"SELECT * FROM staff {where} ORDER BY full_name", params)
    return [dict(r) for r in rows]


def salary_paid_in_period(staff_id: int, period: str) -> float:
    """Total salary already paid to a staff member for a given period label."""
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
        "WHERE staff_id = ? AND kind = 'salary' AND period = ?",
        (staff_id, period),
    )
    return float(row["s"]) if row else 0.0


def total_salary_in_period(period: str) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
        "WHERE kind = 'salary' AND period = ?",
        (period,),
    )
    return float(row["s"]) if row else 0.0


def total_paid_between(start_iso: str, end_iso: str) -> float:
    row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM staff_payments "
        "WHERE pay_date BETWEEN ? AND ?",
        (start_iso, end_iso),
    )
    return float(row["s"]) if row else 0.0
