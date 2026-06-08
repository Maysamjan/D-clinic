"""Reports page with revenue, growth and treatment charts."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
)

from ..models import stats
from .widgets.charts import BarChart, HBarChart, LineChart


class ReportsPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("گزارش‌ها و تحلیل‌ها")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#0f2942;")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(QLabel("بازه:"))
        self.range_combo = QComboBox()
        self.range_combo.addItem("۶ ماه اخیر", 6)
        self.range_combo.addItem("۱۲ ماه اخیر", 12)
        self.range_combo.currentIndexChanged.connect(self.refresh)
        header.addWidget(self.range_combo)
        root.addLayout(header)

        self.revenue_chart = LineChart(color=QColor("#0E9F8E"))
        root.addWidget(self._card("درآمد ماهانه", self.revenue_chart))

        self.growth_chart = BarChart(color=QColor("#0891B2"))
        root.addWidget(self._card("رشد مریض‌ها (ثبت‌نام ماهانه)", self.growth_chart))

        self.treatments_chart = HBarChart(color=QColor("#6366F1"))
        root.addWidget(self._card("رایج‌ترین معالجات", self.treatments_chart))

        root.addStretch(1)

    def _card(self, title, chart):
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        header = QLabel(title)
        header.setObjectName("CardTitle")
        lay.addWidget(header)
        lay.addWidget(chart)
        return card

    def refresh(self):
        months = self.range_combo.currentData() or 6
        self.revenue_chart.set_data(stats.monthly_revenue(months))
        self.growth_chart.set_data(
            [(lbl, float(v)) for lbl, v in stats.patient_growth(months)])
        self.treatments_chart.set_data(
            [(lbl, float(v)) for lbl, v in stats.common_treatments(10)])
