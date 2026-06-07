"""Visit / treatment record model."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db


def create(patient_id: int, treatment_id: Optional[int], treatment_name: str,
           doctor_id: Optional[int], doctor_name: str, visit_date: str,
           cost: float, notes: str = "", tooth: str = "") -> int:
    if not visit_date:
        visit_date = datetime.date.today().isoformat()
    return db.insert(
        """INSERT INTO visits (patient_id, treatment_id, treatment_name,
           doctor_id, doctor_name, visit_date, cost, notes, tooth)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, treatment_id, treatment_name, doctor_id, doctor_name,
         visit_date, cost, notes, tooth),
    )


def update(visit_id: int, treatment_id: Optional[int], treatment_name: str,
           doctor_id: Optional[int], doctor_name: str, visit_date: str,
           cost: float, notes: str = "", tooth: str = "") -> None:
    db.execute(
        """UPDATE visits SET treatment_id = ?, treatment_name = ?,
           doctor_id = ?, doctor_name = ?, visit_date = ?, cost = ?,
           notes = ?, tooth = ? WHERE id = ?""",
        (treatment_id, treatment_name, doctor_id, doctor_name, visit_date,
         cost, notes, tooth, visit_id),
    )


def delete(visit_id: int) -> None:
    db.execute("DELETE FROM visits WHERE id = ?", (visit_id,))


def get(visit_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM visits WHERE id = ?", (visit_id,))
    return dict(row) if row else None


def for_patient(patient_id: int, ascending: bool = True) -> list[dict]:
    """Return all visits for a patient ordered by date (timeline order)."""
    order = "ASC" if ascending else "DESC"
    rows = db.query_all(
        f"SELECT * FROM visits WHERE patient_id = ? "
        f"ORDER BY visit_date {order}, id {order}",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def count_on(date_iso: str) -> int:
    row = db.query_one(
        "SELECT COUNT(*) AS c FROM visits WHERE visit_date = ?", (date_iso,)
    )
    return row["c"] if row else 0
