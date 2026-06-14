"""Treatment plan model — planned future treatments for a patient."""

from __future__ import annotations

from typing import Optional

from ..database import db

# status key -> Persian label (translated for display via i18n)
STATUSES = {
    "planned": "برنامه‌ریزی‌شده",
    "done": "انجام‌شده",
    "cancelled": "لغوشده",
}


def create(patient_id: int, treatment: str, tooth: str = "",
           est_cost: float = 0, status: str = "planned",
           notes: str = "") -> int:
    return db.insert(
        """INSERT INTO treatment_plans
           (patient_id, tooth, treatment, est_cost, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (patient_id, tooth, treatment, est_cost, status, notes),
    )


def update(plan_id: int, treatment: str, tooth: str = "",
           est_cost: float = 0, status: str = "planned",
           notes: str = "") -> None:
    db.execute(
        """UPDATE treatment_plans SET treatment = ?, tooth = ?, est_cost = ?,
           status = ?, notes = ? WHERE id = ?""",
        (treatment, tooth, est_cost, status, notes, plan_id),
    )


def set_status(plan_id: int, status: str) -> None:
    db.execute("UPDATE treatment_plans SET status = ? WHERE id = ?",
               (status, plan_id))


def delete(plan_id: int) -> None:
    db.execute("DELETE FROM treatment_plans WHERE id = ?", (plan_id,))


def get(plan_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM treatment_plans WHERE id = ?", (plan_id,))
    return dict(row) if row else None


def for_patient(patient_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM treatment_plans WHERE patient_id = ? "
        "ORDER BY (status='done') ASC, (status='cancelled') ASC, "
        "priority DESC, id ASC",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def totals(patient_id: int) -> dict:
    """Return {'planned_count', 'planned_cost', 'total_count'} for a patient."""
    row = db.query_one(
        """SELECT
             COUNT(*) AS total_count,
             COALESCE(SUM(CASE WHEN status='planned' THEN 1 ELSE 0 END),0)
               AS planned_count,
             COALESCE(SUM(CASE WHEN status='planned' THEN est_cost ELSE 0 END),0)
               AS planned_cost
           FROM treatment_plans WHERE patient_id = ?""",
        (patient_id,),
    )
    return dict(row) if row else {
        "total_count": 0, "planned_count": 0, "planned_cost": 0}


def patients_with_unfinished() -> list[dict]:
    """Patients who still have at least one 'planned' treatment item."""
    rows = db.query_all(
        """SELECT p.id AS patient_id, p.full_name, p.code, p.phone,
                  COUNT(*) AS planned_count,
                  COALESCE(SUM(tp.est_cost),0) AS planned_cost
           FROM treatment_plans tp
           JOIN patients p ON p.id = tp.patient_id
           WHERE tp.status = 'planned'
           GROUP BY p.id
           ORDER BY planned_count DESC, p.full_name ASC"""
    )
    return [dict(r) for r in rows]


def count_unfinished_patients() -> int:
    row = db.query_one(
        "SELECT COUNT(DISTINCT patient_id) AS c FROM treatment_plans "
        "WHERE status = 'planned'")
    return row["c"] if row else 0
