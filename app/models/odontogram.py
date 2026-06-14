"""Dental chart (odontogram) model — one stored condition per tooth."""

from __future__ import annotations

from ..database import db

# FDI tooth numbering for permanent dentition.
UPPER_RIGHT = ["18", "17", "16", "15", "14", "13", "12", "11"]
UPPER_LEFT = ["21", "22", "23", "24", "25", "26", "27", "28"]
LOWER_RIGHT = ["48", "47", "46", "45", "44", "43", "42", "41"]
LOWER_LEFT = ["31", "32", "33", "34", "35", "36", "37", "38"]

# condition key -> (label, colour)
CONDITIONS = {
    "healthy": ("سالم", "#ffffff"),
    "caries": ("پوسیدگی", "#E11D48"),
    "filled": ("ترمیم‌شده", "#2563EB"),
    "rct": ("عصب‌کشی", "#D97706"),
    "crown": ("روکش", "#CA8A04"),
    "implant": ("ایمپلنت", "#0D9488"),
    "extracted": ("کشیده‌شده", "#94A3B8"),
    "missing": ("غایب", "#E2E8F0"),
}


def get_chart(patient_id: int) -> dict:
    """Return {tooth: {'condition':..., 'note':...}} for a patient."""
    rows = db.query_all(
        "SELECT tooth, condition, note FROM tooth_chart WHERE patient_id = ?",
        (patient_id,),
    )
    return {r["tooth"]: {"condition": r["condition"], "note": r["note"] or ""}
            for r in rows}


def set_tooth(patient_id: int, tooth: str, condition: str, note: str = "") -> None:
    existing = db.query_one(
        "SELECT id FROM tooth_chart WHERE patient_id = ? AND tooth = ?",
        (patient_id, tooth),
    )
    if existing:
        db.execute(
            "UPDATE tooth_chart SET condition = ?, note = ?, "
            "updated_at = datetime('now') WHERE id = ?",
            (condition, note, existing["id"]),
        )
    else:
        db.execute(
            "INSERT INTO tooth_chart (patient_id, tooth, condition, note) "
            "VALUES (?, ?, ?, ?)",
            (patient_id, tooth, condition, note),
        )


def summary(patient_id: int) -> dict:
    """Counts of teeth per non-healthy condition."""
    rows = db.query_all(
        "SELECT condition, COUNT(*) AS c FROM tooth_chart "
        "WHERE patient_id = ? AND condition != 'healthy' GROUP BY condition",
        (patient_id,),
    )
    return {r["condition"]: r["c"] for r in rows}
