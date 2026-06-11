"""Prescription model (with drug line items)."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db


def create(patient_id: int, doctor_name: str, items: list[tuple],
           notes: str = "", presc_date: Optional[str] = None,
           created_by: Optional[int] = None) -> int:
    """Create a prescription. *items* = list of (drug, dosage, instructions)."""
    if not presc_date:
        presc_date = datetime.date.today().isoformat()
    pid = db.insert(
        """INSERT INTO prescriptions (patient_id, doctor_name, presc_date,
           notes, created_by) VALUES (?, ?, ?, ?, ?)""",
        (patient_id, doctor_name, presc_date, notes, created_by),
    )
    for drug, dosage, instr in items:
        db.execute(
            "INSERT INTO prescription_items (prescription_id, drug, dosage, "
            "instructions) VALUES (?, ?, ?, ?)",
            (pid, drug, dosage, instr),
        )
    return pid


def get(presc_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM prescriptions WHERE id = ?", (presc_id,))
    return dict(row) if row else None


def items(presc_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM prescription_items WHERE prescription_id = ? ORDER BY id",
        (presc_id,),
    )
    return [dict(r) for r in rows]


def for_patient(patient_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM prescriptions WHERE patient_id = ? ORDER BY id DESC",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def delete(presc_id: int) -> None:
    db.execute("DELETE FROM prescriptions WHERE id = ?", (presc_id,))
