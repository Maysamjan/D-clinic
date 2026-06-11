"""Dashboard page with stat cards and charts."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
)

from ..models import stats
from ..utils import helpers
from ..services.i18n import t
from .widgets.charts import BarChart, HBarChart, LineChart
from .widgets.stat_card import StatCard


class DashboardPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self.setWidget(container)
        self.root = QVBoxLayout(container)
        self.root.setContentsMargins(26, 24, 26, 24)
        self.root.setSpacing(20)
        self._build()

    def _build(self):
        # Stat cards grid
        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(14)
        self.card_today = StatCard(t("مریض‌های امروز"), "۰", "👥", "#0E9F8E")
        self.card_appts = StatCard(t("نوبت‌های امروز"), "۰", "🗓", "#7C3AED")
        self.card_total = StatCard(t("مجموع مریض‌ها"), "۰", "🗂", "#6366F1")
        self.card_today_rev = StatCard(t("درآمد امروز"), "۰", "💵", "#10A05B")
        self.card_month_rev = StatCard(t("درآمد این ماه"), "۰", "📈", "#0891B2")
        self.card_outstanding = StatCard(t("مطالبات معوقه"), "۰", "⚠", "#E23D5B")
        self.card_new_today = StatCard(t("ثبت‌نام امروز"), "۰", "🆕", "#E0962A")

        for i, card in enumerate([
            self.card_today, self.card_appts, self.card_new_today,
            self.card_total, self.card_today_rev, self.card_month_rev,
            self.card_outstanding,
        ]):
            self.cards_grid.addWidget(card, i // 4, i % 4)
        self.root.addLayout(self.cards_grid)

        # Charts row 1
        row1 = QHBoxLayout()
        row1.setSpacing(14)
        self.revenue_chart = LineChart(color=QColor("#0E9F8E"))
        row1.addWidget(self._chart_card(t("درآمد ماهانه"), self.revenue_chart), 1)
        self.growth_chart = BarChart(color=QColor("#0891B2"))
        row1.addWidget(self._chart_card(t("رشد مریض‌ها"), self.growth_chart), 1)
        self.root.addLayout(row1)

        # Charts row 2
        self.treatments_chart = HBarChart(color=QColor("#6366F1"))
        self.root.addWidget(self._chart_card(t("رایج‌ترین معالجات"), self.treatments_chart))

        self.root.addStretch(1)

    def _chart_card(self, title: str, chart: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        header = QLabel(title)
        header.setObjectName("CardTitle")
        layout.addWidget(header)
        layout.addWidget(chart)
        return card

    def refresh(self):
        import datetime
        from ..models import appointment as appt_model
        s = stats.dashboard_summary()
        self.card_appts.set_value(helpers.jalali_digits(
            appt_model.count_on(datetime.date.today().isoformat())))
        self.card_today.set_value(helpers.jalali_digits(s["today_patients"]))
        self.card_new_today.set_value(helpers.jalali_digits(s["today_registered"]))
        self.card_total.set_value(helpers.jalali_digits(s["total_patients"]))
        self.card_today_rev.set_value(helpers.format_money(s["today_revenue"]))
        self.card_month_rev.set_value(helpers.format_money(s["month_revenue"]))
        self.card_outstanding.set_value(helpers.format_money(s["outstanding"]))

        self.revenue_chart.set_data(stats.monthly_revenue(6))
        self.growth_chart.set_data(
            [(lbl, float(v)) for lbl, v in stats.patient_growth(6)]
        )
        self.treatments_chart.set_data(
            [(lbl, float(v)) for lbl, v in stats.common_treatments(8)]
        )
