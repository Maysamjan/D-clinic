"""Visit / treatment record model."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db


def create(patient_id: int, treatment_id: Optional[int], treatment_name: str,
           doctor_id: Optional[int], doctor_name: str, visit_date: str,
           cost: float, notes: str = "", tooth: str = "",
           staff_id: Optional[int] = None,
           next_visit_date: Optional[str] = None) -> int:
    if not visit_date:
        visit_date = datetime.date.today().isoformat()
    return db.insert(
        """INSERT INTO visits (patient_id, treatment_id, treatment_name,
           doctor_id, doctor_name, visit_date, cost, notes, tooth, staff_id,
           next_visit_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, treatment_id, treatment_name, doctor_id, doctor_name,
         visit_date, cost, notes, tooth, staff_id, next_visit_date or None),
    )


def update(visit_id: int, treatment_id: Optional[int], treatment_name: str,
           doctor_id: Optional[int], doctor_name: str, visit_date: str,
           cost: float, notes: str = "", tooth: str = "",
           staff_id: Optional[int] = None,
           next_visit_date: Optional[str] = None) -> None:
    db.execute(
        """UPDATE visits SET treatment_id = ?, treatment_name = ?,
           doctor_id = ?, doctor_name = ?, visit_date = ?, cost = ?,
           notes = ?, tooth = ?, staff_id = ?, next_visit_date = ?
           WHERE id = ?""",
        (treatment_id, treatment_name, doctor_id, doctor_name, visit_date,
         cost, notes, tooth, staff_id, next_visit_date or None, visit_id),
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


def for_tooth(patient_id: int, tooth: str) -> list[dict]:
    """Return the visit/treatment history recorded for a single tooth."""
    rows = db.query_all(
        "SELECT * FROM visits WHERE patient_id = ? AND tooth = ? "
        "ORDER BY visit_date DESC, id DESC",
        (patient_id, str(tooth)),
    )
    return [dict(r) for r in rows]


def due_followups(window_days: int = 7) -> list[dict]:
    """Patients whose most recent visit set a follow-up date that is now due.

    A follow-up is considered active only on a patient's *latest* visit (so a
    later visit clears it). It is listed when the next-visit date is overdue
    or falls within the next ``window_days`` days.
    """
    horizon = (datetime.date.today()
               + datetime.timedelta(days=window_days)).isoformat()
    rows = db.query_all(
        """
        SELECT v.patient_id, v.next_visit_date, v.treatment_name,
               p.full_name, p.code, p.phone
        FROM visits v
        JOIN patients p ON p.id = v.patient_id
        WHERE v.next_visit_date IS NOT NULL AND v.next_visit_date != ''
          AND v.next_visit_date <= ?
          AND v.id = (
              SELECT v2.id FROM visits v2 WHERE v2.patient_id = v.patient_id
              ORDER BY v2.visit_date DESC, v2.id DESC LIMIT 1)
        ORDER BY v.next_visit_date ASC
        """,
        (horizon,),
    )
    return [dict(r) for r in rows]
