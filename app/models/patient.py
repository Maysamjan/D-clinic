"""Patient model with search and financial aggregation."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db


def _make_code(patient_id: int) -> str:
    return f"P-{patient_id:06d}"


def create(full_name: str, phone: str, gender: str, age: Optional[int],
           address: str, notes: str = "",
           registered_at: Optional[str] = None) -> int:
    """Create a patient and assign a permanent human-friendly code."""
    if not registered_at:
        registered_at = datetime.date.today().isoformat()
    pid = db.insert(
        """INSERT INTO patients (full_name, phone, gender, age, address,
           notes, registered_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (full_name.strip(), phone.strip(), gender, age, address, notes,
         registered_at),
    )
    code = _make_code(pid)
    db.execute("UPDATE patients SET code = ? WHERE id = ?", (code, pid))
    return pid


def update(patient_id: int, full_name: str, phone: str, gender: str,
           age: Optional[int], address: str, notes: str = "") -> None:
    db.execute(
        """UPDATE patients SET full_name = ?, phone = ?, gender = ?, age = ?,
           address = ?, notes = ? WHERE id = ?""",
        (full_name.strip(), phone.strip(), gender, age, address, notes,
         patient_id),
    )


def delete(patient_id: int) -> None:
    db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))


def get(patient_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM patients WHERE id = ?", (patient_id,))
    return dict(row) if row else None


def search(term: str = "", limit: int = 500) -> list[dict]:
    """Search patients by code, phone or name.

    An empty term returns the most recently registered patients.
    """
    term = (term or "").strip()
    if not term:
        rows = db.query_all(
            "SELECT * FROM patients ORDER BY id DESC LIMIT ?", (limit,)
        )
    else:
        like = f"%{term}%"
        rows = db.query_all(
            """SELECT * FROM patients
               WHERE full_name LIKE ? OR phone LIKE ? OR code LIKE ?
               ORDER BY id DESC LIMIT ?""",
            (like, like, like, limit),
        )
    return [dict(r) for r in rows]


def financial_summary(patient_id: int) -> dict:
    """Aggregate visit counts, totals, paid and balance for a patient."""
    total_cost_row = db.query_one(
        "SELECT COALESCE(SUM(cost), 0) AS s, COUNT(*) AS c "
        "FROM visits WHERE patient_id = ?",
        (patient_id,),
    )
    total_paid_row = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM payments WHERE patient_id = ?",
        (patient_id,),
    )
    last_visit_row = db.query_one(
        "SELECT MAX(visit_date) AS d FROM visits WHERE patient_id = ?",
        (patient_id,),
    )
    total_cost = float(total_cost_row["s"]) if total_cost_row else 0.0
    total_paid = float(total_paid_row["s"]) if total_paid_row else 0.0
    return {
        "visits": total_cost_row["c"] if total_cost_row else 0,
        "total_cost": total_cost,
        "total_paid": total_paid,
        "balance": total_cost - total_paid,
        "last_visit": last_visit_row["d"] if last_visit_row else None,
    }


def count() -> int:
    row = db.query_one("SELECT COUNT(*) AS c FROM patients")
    return row["c"] if row else 0


def count_registered_on(date_iso: str) -> int:
    row = db.query_one(
        "SELECT COUNT(*) AS c FROM patients WHERE registered_at = ?",
        (date_iso,),
    )
    return row["c"] if row else 0
