"""Shared UI helper functions."""

from __future__ import annotations

import os

from .. import config
from ..services import jalali


def format_money(value, with_currency: bool = True, persian: bool = True) -> str:
    """Format a number with thousands separators and currency label."""
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    # Drop trailing .0 for whole numbers
    if amount == int(amount):
        text = f"{int(amount):,}"
    else:
        text = f"{amount:,.2f}"
    if persian:
        text = jalali.to_persian_digits(text)
    if with_currency:
        text = f"{text} {config.CURRENCY}"
    return text


def jalali_date(value) -> str:
    """Convert an ISO date/datetime string to a Jalali display string."""
    if not value:
        return "—"
    value = str(value)
    if len(value) > 10:  # has time component
        return jalali.datetime_to_jalali_str(value)
    return jalali.date_to_jalali_str(value)


def load_stylesheet() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "resources", "styles.qss")
    path = os.path.abspath(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def gender_label(value: str) -> str:
    return {"male": "مرد", "female": "زن"}.get(value, value or "—")


def jalali_digits(text) -> str:
    """Convert ASCII digits to Persian digits (safe for any input)."""
    return jalali.to_persian_digits(str(text or ""))
