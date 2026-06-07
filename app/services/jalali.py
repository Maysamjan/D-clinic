"""Jalali (Solar Hijri / Persian-Dari) calendar conversion utilities.

Self-contained implementation so the application has no external
dependencies and works fully offline. The algorithm is the standard
Birashk-free arithmetic conversion that is accurate for the supported
range of years.

All dates are stored in the database as ISO Gregorian strings
(YYYY-MM-DD) and converted to Jalali only for display, which keeps
sorting and comparisons trivial while still showing local dates to the
user.
"""

from __future__ import annotations

import datetime

_PERSIAN_MONTHS = [
    "حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله",
    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت",
]

# Iranian Persian month names (kept for reference / optional use)
_IRANIAN_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

_PERSIAN_WEEKDAYS = [
    "شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه",
]

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_persian_digits(text: str) -> str:
    """Convert ASCII digits in *text* to Persian digits."""
    return str(text).translate(_PERSIAN_DIGITS)


def _div(a: int, b: int) -> int:
    return a // b


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """Convert a Gregorian date to a (jy, jm, jd) Jalali tuple."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (
        365 * gy
        + _div(gy2 + 3, 4)
        - _div(gy2 + 99, 100)
        + _div(gy2 + 399, 400)
        - 80
        + gd
        + g_d_m[gm - 1]
    )
    jy += 33 * _div(days, 12053)
    days %= 12053
    jy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        jy += _div(days - 1, 365)
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + _div(days, 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + _div(days - 186, 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    """Convert a Jalali date to a (gy, gm, gd) Gregorian tuple."""
    if jy > 979:
        gy = 1600
        jy -= 979
    else:
        gy = 621
    days = (
        365 * jy
        + _div(jy, 33) * 8
        + _div((jy % 33) + 3, 4)
        + 78
        + jd
    )
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += (jm - 7) * 30 + 186
    gy += 400 * _div(days, 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * _div(days, 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        gy += _div(days - 1, 365)
        days = (days - 1) % 365
    gd = days + 1
    sal_a = [
        0, 31,
        29 if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
    ]
    gm = 0
    while gm < 13 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1
    return gy, gm, gd


def date_to_jalali_str(d: datetime.date | str, persian_digits: bool = True) -> str:
    """Format a date (or ISO string) as a Jalali ``YYYY/MM/DD`` string."""
    if isinstance(d, str):
        if not d:
            return ""
        try:
            d = datetime.date.fromisoformat(d[:10])
        except ValueError:
            return d
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    text = f"{jy:04d}/{jm:02d}/{jd:02d}"
    return to_persian_digits(text) if persian_digits else text


def datetime_to_jalali_str(value: datetime.datetime | str, persian_digits: bool = True) -> str:
    """Format a datetime (or ISO string) as ``YYYY/MM/DD HH:MM`` Jalali."""
    if isinstance(value, str):
        if not value:
            return ""
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    text = f"{jy:04d}/{jm:02d}/{jd:02d} {value.hour:02d}:{value.minute:02d}"
    return to_persian_digits(text) if persian_digits else text


def jalali_month_name(jm: int) -> str:
    """Return the Dari month name for a Jalali month number (1-12)."""
    return _PERSIAN_MONTHS[(jm - 1) % 12]


def today_jalali() -> tuple[int, int, int]:
    """Return today's date as a Jalali tuple."""
    t = datetime.date.today()
    return gregorian_to_jalali(t.year, t.month, t.day)


def long_jalali(d: datetime.date | str) -> str:
    """Return a long human-friendly Jalali date e.g. ``۱ حمل ۱۴۰۵``."""
    if isinstance(d, str):
        try:
            d = datetime.date.fromisoformat(d[:10])
        except (ValueError, TypeError):
            return d or ""
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return to_persian_digits(f"{jd} {jalali_month_name(jm)} {jy}")
