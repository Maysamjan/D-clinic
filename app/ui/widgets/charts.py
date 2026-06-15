"""Lightweight custom-painted charts (no external dependencies).

Provides a vertical bar chart, a line chart and a horizontal bar chart,
all RTL-friendly and styled to match the application theme.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF, QBrush
from PyQt6.QtWidgets import QWidget

from ...services import i18n, theme
from ...services.i18n import t

_BLUE = QColor("#2563eb")
_GREEN = QColor("#16a34a")


def _bg() -> QColor:
    return QColor(theme.color("chart_bg"))


def _grid() -> QColor:
    return QColor(theme.color("chart_grid"))


def _text() -> QColor:
    return QColor(theme.color("chart_text"))


def _value() -> QColor:
    return QColor(theme.color("chart_value"))


def _fmt(n: float) -> str:
    # Localised digits: Persian in fa mode, ASCII in en mode.
    if n == int(n):
        return i18n.digits(f"{int(n):,}")
    return i18n.digits(f"{n:,.0f}")


class BarChart(QWidget):
    """Vertical bar chart for labelled numeric series."""

    def __init__(self, parent=None, color: QColor = _BLUE):
        super().__init__(parent)
        self._data: list[tuple[str, float]] = []
        self._color = color
        self.setMinimumHeight(220)

    def set_data(self, data: list[tuple[str, float]]):
        self._data = data or []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), _bg())
        w, h = self.width(), self.height()
        left, right, top, bottom = 20, 20, 18, 36
        plot_w = w - left - right
        plot_h = h - top - bottom

        if not self._data:
            p.setPen(_text())
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, t("داده‌ای موجود نیست"))
            return

        max_val = max((v for _, v in self._data), default=0) or 1
        # grid lines
        p.setPen(QPen(_grid(), 1))
        for i in range(5):
            y = top + plot_h * i / 4
            p.drawLine(int(left), int(y), int(w - right), int(y))

        n = len(self._data)
        slot = plot_w / n
        bar_w = min(slot * 0.55, 60)
        font = QFont("Segoe UI", 8)
        p.setFont(font)
        for i, (label, value) in enumerate(self._data):
            bh = (value / max_val) * plot_h
            x = left + slot * i + (slot - bar_w) / 2
            y = top + plot_h - bh
            rect = QRectF(x, y, bar_w, bh)
            p.setBrush(QBrush(self._color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, 6, 6)
            # value label
            p.setPen(_value())
            p.drawText(QRectF(x - 12, y - 18, bar_w + 24, 16),
                       Qt.AlignmentFlag.AlignCenter, _fmt(value))
            # category label
            p.setPen(_text())
            p.drawText(QRectF(left + slot * i, top + plot_h + 4, slot, 28),
                       Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, label)
        p.end()


class LineChart(QWidget):
    """Line chart with filled area for trend data."""

    def __init__(self, parent=None, color: QColor = _GREEN):
        super().__init__(parent)
        self._data: list[tuple[str, float]] = []
        self._color = color
        self.setMinimumHeight(220)

    def set_data(self, data: list[tuple[str, float]]):
        self._data = data or []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), _bg())
        w, h = self.width(), self.height()
        left, right, top, bottom = 20, 20, 18, 36
        plot_w = w - left - right
        plot_h = h - top - bottom

        if not self._data:
            p.setPen(_text())
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, t("داده‌ای موجود نیست"))
            return

        max_val = max((v for _, v in self._data), default=0) or 1
        p.setPen(QPen(_grid(), 1))
        for i in range(5):
            y = top + plot_h * i / 4
            p.drawLine(int(left), int(y), int(w - right), int(y))

        n = len(self._data)
        step = plot_w / max(n - 1, 1)
        points = []
        for i, (_, value) in enumerate(self._data):
            x = left + step * i
            y = top + plot_h - (value / max_val) * plot_h
            points.append(QPointF(x, y))

        # filled area
        area = QPolygonF(points + [QPointF(left + plot_w, top + plot_h),
                                   QPointF(left, top + plot_h)])
        fill = QColor(self._color)
        fill.setAlpha(40)
        p.setBrush(QBrush(fill))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(area)

        # line
        p.setPen(QPen(self._color, 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolyline(QPolygonF(points))

        # points + labels
        font = QFont("Segoe UI", 8)
        p.setFont(font)
        for i, (label, value) in enumerate(self._data):
            pt = points[i]
            p.setBrush(QBrush(self._color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(pt, 4, 4)
            p.setPen(_value())
            p.drawText(QRectF(pt.x() - 26, pt.y() - 20, 52, 16),
                       Qt.AlignmentFlag.AlignCenter, _fmt(value))
            p.setPen(_text())
            p.drawText(QRectF(left + step * i - step / 2, top + plot_h + 4, step, 28),
                       Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, label)
        p.end()


class HBarChart(QWidget):
    """Horizontal bar chart, good for ranked categorical data (RTL)."""

    def __init__(self, parent=None, color: QColor = _BLUE):
        super().__init__(parent)
        self._data: list[tuple[str, float]] = []
        self._color = color
        self.setMinimumHeight(220)

    def set_data(self, data: list[tuple[str, float]]):
        self._data = data or []
        self.setMinimumHeight(max(220, 40 + len(self._data) * 34))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), _bg())
        w, h = self.width(), self.height()

        if not self._data:
            p.setPen(_text())
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, t("داده‌ای موجود نیست"))
            return

        max_val = max((v for _, v in self._data), default=0) or 1
        label_w = 130
        top = 14
        right_pad = 50
        row_h = (h - top - 10) / len(self._data)
        bar_area = w - label_w - right_pad - 16
        font = QFont("Segoe UI", 9)
        p.setFont(font)
        for i, (label, value) in enumerate(self._data):
            y = top + row_h * i
            cy = y + row_h / 2
            bw = (value / max_val) * bar_area
            # label on the right (RTL)
            p.setPen(_value())
            p.drawText(QRectF(w - label_w - 4, y, label_w, row_h),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       label)
            # bar grows from right to left
            bx = w - label_w - 12 - bw
            rect = QRectF(bx, cy - 11, bw, 22)
            p.setBrush(QBrush(self._color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect, 6, 6)
            # value at left end of bar
            p.setPen(_text())
            p.drawText(QRectF(bx - right_pad - 4, cy - 11, right_pad, 22),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       _fmt(value))
        p.end()
