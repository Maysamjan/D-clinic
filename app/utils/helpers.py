"""Shared UI helper functions."""

from __future__ import annotations

import os

from .. import config
from ..services import i18n, jalali


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
    text = i18n.digits(text)
    if with_currency:
        text = f"{text} {config.CURRENCY}"
    return text


def long_date(value) -> str:
    """A long, human date in the active language."""
    if not value:
        return "—"
    if i18n.get_language() == "en":
        import datetime
        try:
            d = datetime.date.fromisoformat(str(value)[:10])
            return d.strftime("%d %B %Y")
        except ValueError:
            return str(value)
    return jalali.long_jalali(value)


def jalali_date(value) -> str:
    """Display a date in the active language (Jalali for fa, Gregorian for en)."""
    if not value:
        return "—"
    value = str(value)
    if i18n.get_language() == "en":
        return value[:16].replace("T", " ") if len(value) > 10 else value[:10]
    if len(value) > 10:  # has time component
        return jalali.datetime_to_jalali_str(value)
    return jalali.date_to_jalali_str(value)


def load_fonts() -> str:
    """Register the bundled Vazirmatn font weights with Qt.

    Returns the resolved family name to use (falls back to a system font
    if the bundled files are unavailable).
    """
    from PyQt6.QtGui import QFontDatabase

    families: list[str] = []
    if os.path.isdir(config.FONTS_DIR):
        for name in sorted(os.listdir(config.FONTS_DIR)):
            if name.lower().endswith((".ttf", ".otf")):
                fid = QFontDatabase.addApplicationFont(
                    os.path.join(config.FONTS_DIR, name))
                if fid != -1:
                    families.extend(QFontDatabase.applicationFontFamilies(fid))
    if any(config.FONT_FAMILY in f for f in families):
        return config.FONT_FAMILY
    return families[0] if families else "Tahoma"


def font_face_css() -> str:
    """Return @font-face CSS embedding the bundled font for print/PDF."""
    weights = {
        "Vazirmatn-Regular.ttf": 400,
        "Vazirmatn-Medium.ttf": 500,
        "Vazirmatn-SemiBold.ttf": 600,
        "Vazirmatn-Bold.ttf": 700,
    }
    rules = []
    for filename, weight in weights.items():
        path = os.path.join(config.FONTS_DIR, filename)
        if os.path.isfile(path):
            url = "file:///" + path.replace("\\", "/").lstrip("/")
            rules.append(
                f"@font-face {{ font-family: 'Vazirmatn'; font-weight: {weight};"
                f" src: url('{url}'); }}"
            )
    return "\n".join(rules)


def load_stylesheet() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "resources", "styles.qss")
    path = os.path.abspath(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def gender_label(value: str) -> str:
    label = {"male": "مرد", "female": "زن"}.get(value, value or "—")
    return i18n.t(label)


def jalali_digits(text) -> str:
    """Localised digits — Persian in fa mode, ASCII in en mode."""
    return i18n.digits(text)
