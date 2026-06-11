"""Interactive dental chart (odontogram) widget.

Shows the 32 permanent teeth (FDI numbering). Clicking a tooth lets the
user set its condition (caries, filled, root canal, crown, implant,
extracted, missing). Conditions are colour-coded and stored per patient.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
)

from ...models import odontogram as odo
from ...services import jalali
from ...services.i18n import is_rtl, t
from .dialog_header import setup_form_dialog

# Short condition codes shown under each tooth number.
_ABBR = {
    "healthy": "", "caries": "C", "filled": "F", "rct": "R",
    "crown": "Cr", "implant": "Im", "extracted": "✕", "missing": "–",
}


def _text_color(bg: str) -> str:
    bg = bg.lstrip("#")
    r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    return "#14253B" if (r * 299 + g * 587 + b * 114) / 1000 > 150 else "#ffffff"


class _ToothDialog(QDialog):
    def __init__(self, parent, tooth, current):
        super().__init__(parent)
        self.setWindowTitle("دندان " + tooth)
        self.setMinimumWidth(360)
        layout = setup_form_dialog(self, "وضعیت دندان " + jalali.to_persian_digits(tooth),
                                   "ثبت وضعیت / معالجه‌ی دندان", "🦷")
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.condition = QComboBox()
        for key, (label, _) in odo.CONDITIONS.items():
            self.condition.addItem(label, key)
        ci = self.condition.findData(current.get("condition", "healthy"))
        if ci >= 0:
            self.condition.setCurrentIndex(ci)
        self.note = QLineEdit(current.get("note", ""))
        form.addRow(t("وضعیت"), self.condition)
        form.addRow(t("یادداشت"), self.note)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class OdontogramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_id = None
        self._buttons: dict[str, QPushButton] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(12)

        hint = QLabel(t("روی هر دندان کلیک کنید تا وضعیت آن را ثبت کنید."))
        hint.setObjectName("SectionHint")
        root.addWidget(hint)

        # Upper jaw
        root.addWidget(self._make_jaw_label("فک بالا"))
        root.addLayout(self._make_row(odo.UPPER_RIGHT + odo.UPPER_LEFT))
        # Lower jaw
        root.addWidget(self._make_jaw_label("فک پایین"))
        root.addLayout(self._make_row(odo.LOWER_RIGHT + odo.LOWER_LEFT))

        root.addSpacing(6)
        root.addWidget(self._make_legend())
        root.addStretch(1)

    def _make_jaw_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#64748b; font-size:12px; font-weight:600;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _make_row(self, teeth):
        row = QHBoxLayout()
        row.setSpacing(4)
        row.setDirection(QHBoxLayout.Direction.LeftToRight)
        row.addStretch(1)
        for idx, tooth_n in enumerate(teeth):
            if idx == len(teeth) // 2:
                row.addSpacing(18)  # gap between the two quadrants
            btn = QPushButton()
            btn.setFixedSize(46, 62)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, tooth=tooth_n: self._edit_tooth(tooth))
            self._buttons[tooth_n] = btn
            row.addWidget(btn)
        row.addStretch(1)
        return row

    def _make_legend(self):
        box = QFrame()
        box.setObjectName("Card")
        lay = QGridLayout(box)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setHorizontalSpacing(14)
        items = list(odo.CONDITIONS.items())
        for i, (key, (label, color)) in enumerate(items):
            chip = QLabel("  ")
            chip.setFixedSize(20, 16)
            chip.setStyleSheet(
                f"background:{color}; border:1px solid #cbd5e1; border-radius:4px;")
            txt = QLabel(label)
            cell = QHBoxLayout()
            cell.setSpacing(6)
            cell.addWidget(chip)
            cell.addWidget(txt)
            w = QWidget()
            w.setLayout(cell)
            lay.addWidget(w, i // 4, i % 4)
        return box

    def set_patient(self, patient_id):
        self.patient_id = patient_id
        self.refresh()

    def _edit_tooth(self, tooth):
        if self.patient_id is None:
            return
        chart = odo.get_chart(self.patient_id)
        current = chart.get(tooth, {"condition": "healthy", "note": ""})
        dlg = _ToothDialog(self, tooth, current)
        if dlg.exec():
            odo.set_tooth(self.patient_id, tooth,
                          dlg.condition.currentData(), dlg.note.text())
            self.refresh()

    def refresh(self):
        if self.patient_id is None:
            return
        chart = odo.get_chart(self.patient_id)
        for tooth, btn in self._buttons.items():
            cond = chart.get(tooth, {}).get("condition", "healthy")
            _, color = odo.CONDITIONS.get(cond, odo.CONDITIONS["healthy"])
            fg = _text_color(color)
            abbr = _ABBR.get(cond, "")
            # Number always on top (bold), condition abbreviation below.
            num = jalali.to_persian_digits(tooth) if is_rtl() else tooth
            btn.setText(f"{num}\n{abbr}")
            btn.setStyleSheet(
                f"QPushButton {{ background:{color}; color:{fg};"
                f" border:1px solid #94a3b8; border-radius:8px;"
                f" font-weight:700; font-size:14px; text-align:center; }}"
                f"QPushButton:hover {{ border:2px solid #0E9F8E; }}")
            note = chart.get(tooth, {}).get("note", "")
            label = odo.CONDITIONS.get(cond, ("", ""))[0]
            tip = t("دندان") + f" {tooth} — {t(label)}"
            if note:
                tip += "\n" + note
            btn.setToolTip(tip)
