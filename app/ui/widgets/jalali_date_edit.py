"""A simple Jalali date entry widget.

The user edits the date in Jalali ``YYYY/MM/DD`` form (Persian digits are
accepted) while the widget exposes the value as an ISO Gregorian string
for storage.
"""

from __future__ import annotations

import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from ...services import jalali

_FA_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


class JalaliDateEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("۱۴۰۵/۰۱/۰۱")
        self.edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        today_btn = QPushButton("امروز")
        today_btn.setObjectName("Secondary")
        today_btn.setFixedWidth(64)
        today_btn.clicked.connect(self.set_today)
        layout.addWidget(self.edit, 1)
        layout.addWidget(today_btn)
        self.set_today()

    def set_today(self):
        jy, jm, jd = jalali.today_jalali()
        self.edit.setText(jalali.to_persian_digits(f"{jy:04d}/{jm:02d}/{jd:02d}"))

    def set_iso(self, iso: str):
        if not iso:
            self.set_today()
            return
        self.edit.setText(jalali.date_to_jalali_str(iso))

    def iso_date(self) -> str | None:
        """Return the entered date as an ISO string, or None if invalid."""
        raw = self.edit.text().strip().translate(_FA_TO_EN)
        raw = raw.replace("-", "/").replace(".", "/")
        parts = [p for p in raw.split("/") if p != ""]
        if len(parts) != 3:
            return None
        try:
            jy, jm, jd = int(parts[0]), int(parts[1]), int(parts[2])
            gy, gm, gd = jalali.jalali_to_gregorian(jy, jm, jd)
            return datetime.date(gy, gm, gd).isoformat()
        except (ValueError, TypeError):
            return None
