"""Salary payroll page (معاشات).

Pay monthly salaries to staff. Pick a period (Jalali month + year), search
or pick an employee from the staff list, see their monthly salary and how
much has already been paid for that period, then record the payment and
print a receipt.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from ..models import staff as staff_model
from ..services import jalali, session
from ..utils import helpers, printing
from ..services.i18n import t
from .widgets.actions import actions_cell, make_button, prepare_table
from .widgets.dialog_header import dialog_header
from .widgets.jalali_date_edit import JalaliDateEdit


def _current_period() -> tuple[int, int]:
    jy, jm, _ = jalali.today_jalali()
    return jy, jm


def period_label(year: int, month: int) -> str:
    return jalali.to_persian_digits(f"{jalali.jalali_month_name(month)} {year}")


# ---------------------------------------------------------------------------
# Salary payment dialog
# ---------------------------------------------------------------------------

class SalaryDialog(QDialog):
    def __init__(self, parent=None, member: dict | None = None,
                 period: str = "", suggested: float = 0):
        super().__init__(parent)
        self.member = member or {}
        self.payment_id = None
        self.setWindowTitle(t("پرداخت معاش"))
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(dialog_header(
            "پرداخت معاش",
            f"{self.member.get('full_name','')} — {self.member.get('position') or ''}",
            "💵"))

        body = QFrame()
        body.setObjectName("DialogBody")
        outer.addWidget(body)
        wrap = QVBoxLayout(body)
        wrap.setContentsMargins(20, 18, 20, 18)
        wrap.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(13)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.period = QLineEdit(period)
        self.period.setReadOnly(True)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setSingleStep(500)
        self.amount.setGroupSeparatorShown(True)
        self.amount.setSuffix(" افغانی")
        self.amount.setValue(max(suggested, 0))
        self.method = QComboBox()
        self.method.addItem(t("نقدی"), "cash")
        self.method.addItem(t("انتقال بانکی"), "bank")
        self.date = JalaliDateEdit()
        self.note = QLineEdit()

        form.addRow(t("دوره"), self.period)
        form.addRow(t("مبلغ معاش *"), self.amount)
        form.addRow(t("روش پرداخت"), self.method)
        form.addRow(t("تاریخ"), self.date)
        form.addRow(t("یادداشت"), self.note)
        wrap.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ثبت و رسید")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        wrap.addWidget(buttons)

    def _save(self):
        if self.amount.value() <= 0:
            QMessageBox.warning(self, t("خطا"), t("مبلغ معاش باید بیشتر از صفر باشد."))
            return
        uid = session.current_user["id"] if session.current_user else None
        self.payment_id = staff_model.add_payment(
            self.member["id"], self.amount.value(), "salary",
            self.period.text(), self.method.currentData(),
            self.date.iso_date(), self.note.text(), created_by=uid)
        self.accept()


# ---------------------------------------------------------------------------
# Salary page
# ---------------------------------------------------------------------------

class SalaryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        # Period + search toolbar
        bar = QHBoxLayout()
        bar.setSpacing(10)
        bar.addWidget(QLabel(t("دوره معاش:")))
        self.month = QComboBox()
        for m in range(1, 13):
            self.month.addItem(jalali.jalali_month_name(m), m)
        self.year = QComboBox()
        cy, cm = _current_period()
        for y in range(cy - 2, cy + 2):
            self.year.addItem(jalali.to_persian_digits(str(y)), y)
        self.month.setCurrentIndex(cm - 1)
        self.year.setCurrentIndex(2)  # current year (cy-2 .. cy+1 -> index 2 = cy)
        self.month.currentIndexChanged.connect(self.refresh)
        self.year.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.month)
        bar.addWidget(self.year)

        self.search = QLineEdit()
        self.search.setPlaceholderText(t("🔍  جستجوی کارمند با نام، کود یا وظیفه ..."))
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)
        layout.addLayout(bar)

        self.summary = QLabel()
        self.summary.setObjectName("SectionHint")
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            t("کود"), t("نام"), t("وظیفه"), t("معاش ماهانه"), t("پرداخت‌شده (دوره)"),
            t("باقیمانده"), t("وضعیت"), t("عملیات")])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        prepare_table(self.table)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 150)
        layout.addWidget(self.table)

    def _period(self) -> str:
        return period_label(self.year.currentData(), self.month.currentData())

    def _pay(self, member):
        period = self._period()
        paid = staff_model.salary_paid_in_period(member["id"], period)
        remaining = max(float(member.get("base_salary") or 0) - paid, 0)
        suggested = remaining if remaining > 0 else float(member.get("base_salary") or 0)
        dlg = SalaryDialog(self, member=member, period=period, suggested=suggested)
        if dlg.exec():
            self.refresh()
            if dlg.payment_id and QMessageBox.question(
                self, t("رسید"), t("رسید پرداخت معاش چاپ شود؟")
            ) == QMessageBox.StandardButton.Yes:
                printing.print_or_pdf(
                    self, printing.staff_receipt_html(dlg.payment_id),
                    "رسید معاش")

    def refresh(self):
        period = self._period()
        staff = staff_model.search(self.search.text(), active_only=True)
        total = staff_model.total_salary_in_period(period)
        self.summary.setText(
            f"دوره: {period}  •  مجموع معاشات پرداخت‌شده این دوره: "
            f"{helpers.format_money(total)}")

        self.table.setRowCount(0)
        for m in staff:
            base = float(m.get("base_salary") or 0)
            paid = staff_model.salary_paid_in_period(m["id"], period)
            remaining = base - paid
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_digits(m.get("code", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(m.get("full_name", "")))
            self.table.setItem(r, 2, QTableWidgetItem(m.get("position") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(helpers.format_money(base)))
            self.table.setItem(r, 4, QTableWidgetItem(helpers.format_money(paid)))
            self.table.setItem(r, 5, QTableWidgetItem(
                helpers.format_money(remaining)))
            # status
            if base <= 0:
                status, color = t("بدون معاش ثابت"), "#64748B"
            elif paid <= 0:
                status, color = t("پرداخت‌نشده"), "#E11D48"
            elif remaining > 0.5:
                status, color = t("ناقص"), "#D97706"
            else:
                status, color = t("پرداخت‌شده"), "#0C7A43"
            st = QTableWidgetItem(status)
            from PyQt6.QtGui import QColor
            st.setForeground(QColor(color))
            self.table.setItem(r, 6, st)
            self.table.setCellWidget(r, 7, actions_cell([
                make_button("پرداخت", "success", "ثبت پرداخت معاش",
                            lambda mm=m: self._pay(mm))]))
