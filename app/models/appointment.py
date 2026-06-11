"""Appointment / scheduling model."""

from __future__ import annotations

import datetime
from typing import Optional

from ..database import db

STATUSES = {
    "scheduled": "در انتظار",
    "done": "انجام‌شده",
    "cancelled": "لغو‌شده",
    "noshow": "حاضر نشد",
}


def create(patient_id: Optional[int], patient_name: str, phone: str,
           staff_id: Optional[int], doctor_name: str, appt_date: str,
           appt_time: str, reason: str = "", notes: str = "") -> int:
    if not appt_date:
        appt_date = datetime.date.today().isoformat()
    return db.insert(
        """INSERT INTO appointments (patient_id, patient_name, phone, staff_id,
           doctor_name, appt_date, appt_time, reason, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, patient_name.strip(), phone.strip(), staff_id,
         doctor_name, appt_date, appt_time.strip(), reason, notes),
    )


def update(appt_id: int, patient_id: Optional[int], patient_name: str,
           phone: str, staff_id: Optional[int], doctor_name: str,
           appt_date: str, appt_time: str, reason: str, notes: str) -> None:
    db.execute(
        """UPDATE appointments SET patient_id = ?, patient_name = ?, phone = ?,
           staff_id = ?, doctor_name = ?, appt_date = ?, appt_time = ?,
           reason = ?, notes = ? WHERE id = ?""",
        (patient_id, patient_name.strip(), phone.strip(), staff_id,
         doctor_name, appt_date, appt_time.strip(), reason, notes, appt_id),
    )


def set_status(appt_id: int, status: str) -> None:
    db.execute("UPDATE appointments SET status = ? WHERE id = ?",
               (status, appt_id))


def delete(appt_id: int) -> None:
    db.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))


def get(appt_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM appointments WHERE id = ?", (appt_id,))
    return dict(row) if row else None


def for_date(date_iso: str) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM appointments WHERE appt_date = ? "
        "ORDER BY appt_time, id",
        (date_iso,),
    )
    return [dict(r) for r in rows]


def upcoming(limit: int = 50) -> list[dict]:
    today = datetime.date.today().isoformat()
    rows = db.query_all(
        "SELECT * FROM appointments WHERE appt_date >= ? AND status = 'scheduled' "
        "ORDER BY appt_date, appt_time LIMIT ?",
        (today, limit),
    )
    return [dict(r) for r in rows]


def for_patient(patient_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM appointments WHERE patient_id = ? "
        "ORDER BY appt_date DESC, appt_time DESC",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def count_on(date_iso: str) -> int:
    row = db.query_one(
        "SELECT COUNT(*) AS c FROM appointments WHERE appt_date = ?", (date_iso,))
    return row["c"] if row else 0
