"""Clinic expenses, profit/loss summary and daily cash report."""

from __future__ import annotations

import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget
)

from ..models import expense as expense_model
from ..services import jalali, session
from ..utils import helpers, printing
from ..services.i18n import t
from .widgets.actions import actions_cell, make_button, prepare_table
from .widgets.dialog_header import setup_form_dialog
from .widgets.jalali_date_edit import JalaliDateEdit


class ExpenseDialog(QDialog):
    def __init__(self, parent=None, expense: dict | None = None):
        super().__init__(parent)
        self.expense = expense
        self.setWindowTitle("ویرایش مصرف" if expense else "ثبت مصرف جدید")
        self.setMinimumWidth(420)
        layout = setup_form_dialog(
            self, "ویرایش مصرف" if expense else "ثبت مصرف جدید",
            "مصارف و هزینه‌های کلینیک", "🧾")
        form = QFormLayout()
        form.setSpacing(13)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.category = QComboBox()
        for key, label in expense_model.CATEGORIES.items():
            self.category.addItem(label, key)
        self.description = QLineEdit()
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setGroupSeparatorShown(True)
        self.amount.setSuffix(" افغانی")
        self.paid_to = QLineEdit()
        self.date = JalaliDateEdit()

        form.addRow(t("دسته"), self.category)
        form.addRow(t("شرح *"), self.description)
        form.addRow(t("مبلغ *"), self.amount)
        form.addRow(t("پرداخت به"), self.paid_to)
        form.addRow(t("تاریخ"), self.date)
        layout.addLayout(form)

        if expense:
            i = self.category.findData(expense.get("category"))
            if i >= 0:
                self.category.setCurrentIndex(i)
            self.description.setText(expense.get("description", ""))
            self.amount.setValue(float(expense.get("amount") or 0))
            self.paid_to.setText(expense.get("paid_to", ""))
            self.date.set_iso(expense.get("expense_date"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        if not self.description.text().strip():
            QMessageBox.warning(self, t("خطا"), t("شرح مصرف الزامی است."))
            return
        if self.amount.value() <= 0:
            QMessageBox.warning(self, t("خطا"), t("مبلغ باید بیشتر از صفر باشد."))
            return
        uid = session.current_user["id"] if session.current_user else None
        if self.expense:
            expense_model.update(
                self.expense["id"], self.category.currentData(),
                self.description.text(), self.amount.value(),
                self.date.iso_date(), self.paid_to.text())
        else:
            expense_model.create(
                self.category.currentData(), self.description.text(),
                self.amount.value(), self.date.iso_date(),
                self.paid_to.text(), created_by=uid)
        self.accept()


def _card(label, color):
    box = QFrame()
    box.setObjectName("Card")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(16, 12, 16, 12)
    val = QLabel("—")
    val.setStyleSheet(f"font-size:21px; font-weight:700; color:{color};")
    cap = QLabel(label)
    cap.setStyleSheet("color:#64748b; font-size:12px;")
    lay.addWidget(val)
    lay.addWidget(cap)
    return box, val


class ExpensesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        # Period + actions
        bar = QHBoxLayout()
        bar.setSpacing(10)
        bar.addWidget(QLabel(t("دوره:")))
        self.month = QComboBox()
        for m in range(1, 13):
            self.month.addItem(jalali.jalali_month_name(m), m)
        self.year = QComboBox()
        jy, jm, _ = jalali.today_jalali()
        for y in range(jy - 2, jy + 2):
            self.year.addItem(jalali.to_persian_digits(str(y)), y)
        self.month.setCurrentIndex(jm - 1)
        self.year.setCurrentIndex(2)
        self.month.currentIndexChanged.connect(self.refresh)
        self.year.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.month)
        bar.addWidget(self.year)
        bar.addStretch(1)
        daily_btn = QPushButton(t("🖨 راپور روزانه صندوق"))
        daily_btn.setObjectName("Secondary")
        daily_btn.clicked.connect(self._daily_report)
        add_btn = QPushButton(t("➕ ثبت مصرف"))
        add_btn.clicked.connect(self._add)
        bar.addWidget(daily_btn)
        bar.addWidget(add_btn)
        layout.addLayout(bar)

        # Profit/loss cards
        grid = QGridLayout()
        grid.setSpacing(12)
        self.box_income, self.val_income = _card(t("درآمد (دریافتی‌ها)"), "#0C7A43")
        self.box_exp, self.val_exp = _card(t("مصارف"), "#D97706")
        self.box_staff, self.val_staff = _card(t("پرداخت به کارمندان"), "#2563EB")
        self.box_net, self.val_net = _card(t("سود خالص"), "#0E9F8E")
        for i, b in enumerate([self.box_income, self.box_exp, self.box_staff, self.box_net]):
            grid.addWidget(b, 0, i)
        layout.addLayout(grid)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            t("تاریخ"), t("دسته"), t("شرح"), t("پرداخت به"), t("مبلغ"), t("عملیات")])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        prepare_table(self.table)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def _span(self):
        y = self.year.currentData()
        m = self.month.currentData()
        start = datetime.date(*jalali.jalali_to_gregorian(y, m, 1))
        last_day = 31 if m <= 6 else 30
        # clamp to valid gregorian end
        try:
            end = datetime.date(*jalali.jalali_to_gregorian(y, m, last_day))
        except ValueError:
            end = datetime.date(*jalali.jalali_to_gregorian(y, m, 29))
        return start.isoformat(), end.isoformat()

    def _add(self):
        dlg = ExpenseDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit(self, e):
        dlg = ExpenseDialog(self, expense=e)
        if dlg.exec():
            self.refresh()

    def _delete(self, eid):
        if QMessageBox.question(
            self, t("حذف"), t("این مصرف حذف شود؟")
        ) == QMessageBox.StandardButton.Yes:
            expense_model.delete(eid)
            self.refresh()

    def _daily_report(self):
        html = printing.daily_report_html(datetime.date.today().isoformat())
        printing.print_or_pdf(self, html, "راپور روزانه")

    def refresh(self):
        start, end = self._span()
        pl = expense_model.profit_loss(start, end)
        self.val_income.setText(helpers.format_money(pl["income"]))
        self.val_exp.setText(helpers.format_money(pl["expenses"]))
        self.val_staff.setText(helpers.format_money(pl["staff_paid"]))
        self.val_net.setText(helpers.format_money(pl["net"]))
        self.val_net.setStyleSheet(
            "font-size:21px; font-weight:700; color:%s;"
            % ("#0C7A43" if pl["net"] >= 0 else "#E11D48"))

        self.table.setRowCount(0)
        for e in expense_model.between(start, end):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_date(e.get("expense_date"))))
            self.table.setItem(r, 1, QTableWidgetItem(
                t(expense_model.CATEGORIES.get(e.get("category"), ""))))
            self.table.setItem(r, 2, QTableWidgetItem(e.get("description") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(e.get("paid_to") or "—"))
            self.table.setItem(r, 4, QTableWidgetItem(
                helpers.format_money(e.get("amount", 0))))
            self.table.setCellWidget(r, 5, actions_cell([
                make_button("ویرایش", "default", "ویرایش",
                            lambda ee=e: self._edit(ee)),
                make_button("حذف", "danger", "حذف",
                            lambda eid=e["id"]: self._delete(eid)),
            ]))
