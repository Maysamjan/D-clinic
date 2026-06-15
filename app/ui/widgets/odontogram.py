"""Interactive dental chart (odontogram) widget.

Shows the 32 permanent teeth (FDI numbering) as two anatomical dental
arches (upper jaw and lower jaw) drawn with QPainter. Each tooth is a
tooth-shaped, colour-coded, numbered and clickable shape; clicking opens a
dialog to set its condition. A clear, always-readable legend sits below.
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget
)

from ...models import odontogram as odo
from ...services import jalali, theme
from ...services.i18n import digits, t
from .dialog_header import setup_form_dialog

# Short condition codes shown on each tooth.
_ABBR = {
    "healthy": "", "caries": "C", "filled": "F", "rct": "R",
    "crown": "Cr", "implant": "Im", "extracted": "✕", "missing": "–",
}


def _text_color(bg: str) -> str:
    bg = bg.lstrip("#")
    r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    return "#14253B" if (r * 299 + g * 587 + b * 114) / 1000 > 150 else "#ffffff"


# ---------------------------------------------------------------------------
# Tooth condition dialog
# ---------------------------------------------------------------------------

class _ToothDialog(QDialog):
    def __init__(self, parent, tooth, current, history=None):
        super().__init__(parent)
        self.setWindowTitle(t("دندان") + " " + tooth)
        self.setMinimumWidth(380)
        layout = setup_form_dialog(
            self, t("وضعیت دندان") + " " + digits(tooth),
            "ثبت وضعیت / معالجه‌ی دندان", "🦷")
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.condition = QComboBox()
        for key, (label, _c) in odo.CONDITIONS.items():
            self.condition.addItem(t(label), key)
        ci = self.condition.findData(current.get("condition", "healthy"))
        if ci >= 0:
            self.condition.setCurrentIndex(ci)
        self.note = QLineEdit(current.get("note", ""))
        form.addRow(t("وضعیت"), self.condition)
        form.addRow(t("یادداشت"), self.note)
        layout.addLayout(form)

        # Per-tooth treatment history
        hist_title = QLabel(t("سوابق معالجه این دندان"))
        hist_title.setStyleSheet("font-weight:bold; color:#0A6B61; margin-top:6px;")
        layout.addWidget(hist_title)
        if history:
            from ...utils import helpers
            box = QVBoxLayout()
            for v in history[:8]:
                row = QLabel("• " + helpers.jalali_date(v.get("visit_date"))
                             + " — " + (v.get("treatment_name") or t("ویزیت"))
                             + (("  (" + (v.get("doctor_name") or "") + ")")
                                if v.get("doctor_name") else ""))
                row.setStyleSheet(
                    "color:" + theme.color("muted") + "; font-size:12px;")
                row.setWordWrap(True)
                box.addWidget(row)
            layout.addLayout(box)
        else:
            empty = QLabel(t("هنوز معالجه‌ای برای این دندان ثبت نشده است."))
            empty.setStyleSheet("color:#94A3B8; font-size:12px;")
            layout.addWidget(empty)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(t("ذخیره"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("لغو"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# ---------------------------------------------------------------------------
# Painted dental arches
# ---------------------------------------------------------------------------

class _ArchCanvas(QWidget):
    """Draws the upper and lower dental arches and reports tooth clicks."""

    toothClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chart: dict = {}
        self._rects: dict[str, QRectF] = {}
        self._hover: str | None = None
        self.setMinimumHeight(420)
        self.setMouseTracking(True)
        self._upper = odo.UPPER_RIGHT + odo.UPPER_LEFT
        self._lower = odo.LOWER_RIGHT + odo.LOWER_LEFT

    def set_chart(self, chart: dict):
        self._chart = chart or {}
        self.update()

    # -- painting --------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#F7FAFC"))
        w, h = self.width(), self.height()
        self._rects = {}

        # arch captions
        p.setPen(QColor("#64748b"))
        p.setFont(QFont("Vazirmatn", 9, QFont.Weight.Bold))
        p.drawText(QRectF(0, 4, w, 16), Qt.AlignmentFlag.AlignHCenter, t("فک بالا"))
        p.drawText(QRectF(0, h / 2 + 4, w, 16),
                   Qt.AlignmentFlag.AlignHCenter, t("فک پایین"))

        self._draw_arch(p, self._upper, True, w, h)
        self._draw_arch(p, self._lower, False, w, h)
        p.end()

    def _draw_arch(self, p, teeth, is_upper, w, h):
        margin = 42
        usable = max(w - 2 * margin, 100)
        n = len(teeth)
        slot = usable / n
        tw = min(slot * 0.82, 30)
        th = tw * 1.4
        amp = 56
        top_zone = 24
        for i, tooth in enumerate(teeth):
            nx = (i + 0.5) / n
            x = margin + nx * usable
            c = (nx - 0.5) * 2.0
            curve = c * c  # 0 at centre, 1 at the molars
            if is_upper:
                y = top_zone + (1 - curve) * amp
            else:
                y = (h - top_zone - th) - (1 - curve) * amp
            rect = QRectF(x - tw / 2, y, tw, th)
            self._rects[tooth] = rect
            cond = self._chart.get(tooth, {}).get("condition", "healthy")
            color = odo.CONDITIONS.get(cond, odo.CONDITIONS["healthy"])[1]

            # tooth shape
            path = QPainterPath()
            path.addRoundedRect(rect, tw * 0.38, tw * 0.32)
            p.setBrush(QColor(color))
            if tooth == self._hover:
                p.setPen(QPen(QColor("#0E9F8E"), 2.4))
            else:
                p.setPen(QPen(QColor("#94A3B8"), 1.1))
            p.drawPath(path)

            # extracted / missing → red cross
            if cond in ("extracted", "missing"):
                p.setPen(QPen(QColor("#E11D48"), 2))
                p.drawLine(rect.topLeft(), rect.bottomRight())
                p.drawLine(rect.topRight(), rect.bottomLeft())

            # condition code inside the tooth
            abbr = _ABBR.get(cond, "")
            if abbr and cond not in ("extracted", "missing"):
                p.setPen(QColor(_text_color(color)))
                p.setFont(QFont("Vazirmatn", 8, QFont.Weight.Bold))
                p.drawText(rect, Qt.AlignmentFlag.AlignCenter, abbr)

            # FDI number (outside the tooth, always readable)
            p.setPen(QColor("#334155"))
            p.setFont(QFont("Vazirmatn", 8, QFont.Weight.Bold))
            num = digits(tooth)
            if is_upper:
                ny = rect.top() - 15
            else:
                ny = rect.bottom() + 1
            p.drawText(QRectF(x - 16, ny, 32, 14),
                       Qt.AlignmentFlag.AlignCenter, num)

    # -- interaction -----------------------------------------------------
    def _tooth_at(self, pos):
        for tooth, rect in self._rects.items():
            if rect.adjusted(-2, -2, 2, 2).contains(pos):
                return tooth
        return None

    def mousePressEvent(self, event):
        tooth = self._tooth_at(event.position())
        if tooth:
            self.toothClicked.emit(tooth)

    def mouseMoveEvent(self, event):
        tooth = self._tooth_at(event.position())
        if tooth != self._hover:
            self._hover = tooth
            self.setCursor(Qt.CursorShape.PointingHandCursor if tooth
                           else Qt.CursorShape.ArrowCursor)
            self.update()


# ---------------------------------------------------------------------------
# Full widget (arches + legend)
# ---------------------------------------------------------------------------

class OdontogramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_id = None
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(10)

        hint = QLabel(t("روی هر دندان کلیک کنید تا وضعیت آن را ثبت کنید."))
        hint.setObjectName("SectionHint")
        root.addWidget(hint)

        self.canvas = _ArchCanvas()
        self.canvas.toothClicked.connect(self._edit_tooth)
        root.addWidget(self.canvas, 1)

        root.addWidget(self._make_legend())

    def _make_legend(self):
        box = QFrame()
        box.setObjectName("Card")
        lay = QGridLayout(box)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setHorizontalSpacing(20)
        lay.setVerticalSpacing(10)
        items = list(odo.CONDITIONS.items())
        for i, (key, (label, color)) in enumerate(items):
            item = QWidget()
            il = QHBoxLayout(item)
            il.setContentsMargins(0, 0, 0, 0)
            il.setSpacing(8)
            chip = QLabel()
            chip.setFixedSize(20, 20)
            chip.setStyleSheet(
                f"background:{color}; border:1px solid #94A3B8;"
                f"border-radius:5px;")
            txt = QLabel(t(label))
            txt.setStyleSheet("color:#1F2A37; font-size:13px; font-weight:600;")
            il.addWidget(chip)
            il.addWidget(txt)
            il.addStretch(1)
            lay.addWidget(item, i // 4, i % 4)
        return box

    def set_patient(self, patient_id):
        self.patient_id = patient_id
        self.refresh()

    def _edit_tooth(self, tooth):
        if self.patient_id is None:
            return
        chart = odo.get_chart(self.patient_id)
        current = chart.get(tooth, {"condition": "healthy", "note": ""})
        from ...models import visit as visit_model
        history = visit_model.for_tooth(self.patient_id, tooth)
        dlg = _ToothDialog(self, tooth, current, history=history)
        if dlg.exec():
            odo.set_tooth(self.patient_id, tooth,
                          dlg.condition.currentData(), dlg.note.text())
            self.refresh()

    def refresh(self):
        if self.patient_id is None:
            return
        self.canvas.set_chart(odo.get_chart(self.patient_id))
