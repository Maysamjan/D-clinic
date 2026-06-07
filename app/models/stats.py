"""Aggregate statistics for the dashboard and reports."""

from __future__ import annotations

import datetime

from ..database import db
from . import patient, payment, visit


def dashboard_summary() -> dict:
    """Return the key metrics shown on the dashboard cards."""
    today = datetime.date.today()
    today_iso = today.isoformat()
    month_start = today.replace(day=1).isoformat()

    outstanding_row = db.query_one(
        """SELECT
             (SELECT COALESCE(SUM(cost), 0) FROM visits) -
             (SELECT COALESCE(SUM(amount), 0) FROM payments) AS bal"""
    )
    outstanding = float(outstanding_row["bal"]) if outstanding_row else 0.0

    return {
        "today_patients": visit.count_on(today_iso),
        "today_registered": patient.count_registered_on(today_iso),
        "total_patients": patient.count(),
        "today_revenue": payment.total_on(today_iso),
        "month_revenue": payment.total_between(month_start, today_iso),
        "outstanding": max(outstanding, 0.0),
    }


def monthly_revenue(months: int = 6) -> list[tuple[str, float]]:
    """Return (jalali_label, amount) revenue for the last *months* months."""
    from ..services import jalali

    today = datetime.date.today()
    result: list[tuple[str, float]] = []
    year, month = today.year, today.month
    spans = []
    for _ in range(months):
        spans.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    spans.reverse()
    for (y, m) in spans:
        start = datetime.date(y, m, 1)
        if m == 12:
            end = datetime.date(y, 12, 31)
        else:
            end = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
        amount = payment.total_between(start.isoformat(), end.isoformat())
        jy, jm, _ = jalali.gregorian_to_jalali(y, m, 15)
        label = jalali.to_persian_digits(f"{jalali.jalali_month_name(jm)} {jy}")
        result.append((label, amount))
    return result


def patient_growth(months: int = 6) -> list[tuple[str, int]]:
    """Return (jalali_label, new_patient_count) for the last *months* months."""
    from ..services import jalali

    today = datetime.date.today()
    result: list[tuple[str, int]] = []
    year, month = today.year, today.month
    spans = []
    for _ in range(months):
        spans.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    spans.reverse()
    for (y, m) in spans:
        start = datetime.date(y, m, 1)
        if m == 12:
            end = datetime.date(y, 12, 31)
        else:
            end = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
        row = db.query_one(
            "SELECT COUNT(*) AS c FROM patients WHERE registered_at BETWEEN ? AND ?",
            (start.isoformat(), end.isoformat()),
        )
        jy, jm, _ = jalali.gregorian_to_jalali(y, m, 15)
        label = jalali.to_persian_digits(f"{jalali.jalali_month_name(jm)} {jy}")
        result.append((label, row["c"] if row else 0))
    return result


def common_treatments(limit: int = 8) -> list[tuple[str, int]]:
    """Return the most frequently performed treatments."""
    rows = db.query_all(
        """SELECT COALESCE(NULLIF(treatment_name,''), 'نامشخص') AS name,
           COUNT(*) AS c FROM visits
           GROUP BY treatment_name ORDER BY c DESC LIMIT ?""",
        (limit,),
    )
    return [(r["name"], r["c"]) for r in rows]
