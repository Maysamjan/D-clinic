"""Dashboard page with stat cards and charts."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
)

from ..models import stats
from ..models import treatment_plan as plan_model
from ..models import visit as visit_model
from ..utils import helpers
from ..services.i18n import t
from .widgets.charts import BarChart, HBarChart, LineChart
from .widgets.stat_card import StatCard


class DashboardPage(QScrollArea):
    open_patient = pyqtSignal(int)

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
        self.card_followup = StatCard(t("مراجعه‌ بعدی (یادآوری)"), "۰", "📅", "#0EA5A0")
        self.card_unfinished = StatCard(t("معالجات ناتمام"), "۰", "📝", "#D97706")

        self._cards = [
            self.card_today, self.card_appts, self.card_new_today,
            self.card_total, self.card_today_rev, self.card_month_rev,
            self.card_outstanding, self.card_followup, self.card_unfinished,
        ]
        self._card_cols = 0
        self._relayout_cards(4)
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

        # Follow-up & recall row
        recall_row = QHBoxLayout()
        recall_row.setSpacing(14)
        self.followup_list = self._list_card(t("📅 مریض‌های نیازمند مراجعه بعدی"))
        self.unfinished_list = self._list_card(t("📝 مریض‌های با معالجه‌ی ناتمام"))
        recall_row.addWidget(self.followup_list["card"], 1)
        recall_row.addWidget(self.unfinished_list["card"], 1)
        self.root.addLayout(recall_row)

        self.root.addStretch(1)

    def _list_card(self, title: str) -> dict:
        from PyQt6.QtWidgets import QTableWidget, QAbstractItemView, QHeaderView
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        header = QLabel(title)
        header.setObjectName("CardTitle")
        layout.addWidget(header)
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels([t("مریض"), t("تلفن"), t("جزئیات")])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(180)
        table.doubleClicked.connect(
            lambda idx, tb=table: self._open_from_list(tb, idx))
        layout.addWidget(table)
        empty = QLabel(t("موردی وجود ندارد."))
        empty.setStyleSheet("color:#94A3B8; font-size:12px;")
        layout.addWidget(empty)
        return {"card": card, "table": table, "empty": empty}

    def _open_from_list(self, table, index):
        from PyQt6.QtWidgets import QTableWidgetItem  # noqa: F401
        row = index.row()
        item = table.item(row, 0)
        if item is None:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid:
            self.open_patient.emit(int(pid))

    def _relayout_cards(self, cols: int):
        if cols == self._card_cols:
            return
        self._card_cols = cols
        while self.cards_grid.count():
            self.cards_grid.takeAt(0)
        for i, card in enumerate(self._cards):
            self.cards_grid.addWidget(card, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.viewport().width()
        cols = 4 if w > 1080 else 3 if w > 800 else 2 if w > 540 else 1
        self._relayout_cards(cols)

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

        # Follow-up & recall
        due = visit_model.due_followups(window_days=7)
        unfinished = plan_model.patients_with_unfinished()
        self.card_followup.set_value(helpers.jalali_digits(len(due)))
        self.card_unfinished.set_value(helpers.jalali_digits(len(unfinished)))
        self._fill_list(
            self.followup_list, due,
            lambda r: helpers.jalali_date(r.get("next_visit_date")))
        self._fill_list(
            self.unfinished_list, unfinished,
            lambda r: (helpers.jalali_digits(r.get("planned_count")) + t(" مورد")
                       + " · " + helpers.format_money(r.get("planned_cost", 0))))

    def _fill_list(self, widgets, rows, detail_fn):
        from PyQt6.QtWidgets import QTableWidgetItem
        table = widgets["table"]
        table.setRowCount(0)
        for rec in rows:
            r = table.rowCount()
            table.insertRow(r)
            name_item = QTableWidgetItem(rec.get("full_name") or "—")
            name_item.setData(Qt.ItemDataRole.UserRole, rec.get("patient_id"))
            table.setItem(r, 0, name_item)
            table.setItem(r, 1, QTableWidgetItem(
                helpers.jalali_digits(rec.get("phone")) if rec.get("phone") else "—"))
            table.setItem(r, 2, QTableWidgetItem(detail_fn(rec)))
        widgets["empty"].setVisible(not rows)
        table.setVisible(bool(rows))
