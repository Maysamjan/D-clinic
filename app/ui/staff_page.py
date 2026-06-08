"""Staff / doctors registry and payroll page.

Register clinic personnel, see the commission they earn from the
treatments they perform, record salary / commission / bonus payouts, and
print a payment receipt for each payout.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget
)

from ..models import staff as staff_model
from ..services import session
from ..utils import helpers, printing
from .widgets.actions import actions_cell, make_button, prepare_table
from .widgets.jalali_date_edit import JalaliDateEdit

POSITIONS = ["داکتر", "نرس", "پذیرش", "تکنیشن", "خدمات", "محاسب", "مدیر"]


# ---------------------------------------------------------------------------
# Staff add / edit dialog
# ---------------------------------------------------------------------------

class StaffDialog(QDialog):
    def __init__(self, parent=None, member: dict | None = None):
        super().__init__(parent)
        self.member = member
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ویرایش کارمند" if member else "ثبت کارمند / داکتر جدید")
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.full_name = QLineEdit()
        self.position = QComboBox()
        self.position.setEditable(True)
        self.position.addItems(POSITIONS)
        self.phone = QLineEdit()
        self.pay_type = QComboBox()
        for key, label in staff_model.PAY_TYPES.items():
            self.pay_type.addItem(label, key)
        self.base_salary = QDoubleSpinBox()
        self.base_salary.setRange(0, 100_000_000)
        self.base_salary.setSingleStep(1000)
        self.base_salary.setGroupSeparatorShown(True)
        self.base_salary.setSuffix(" افغانی")
        self.commission = QDoubleSpinBox()
        self.commission.setRange(0, 100)
        self.commission.setSuffix(" ٪")
        self.is_provider = QCheckBox("این شخص معالجه انجام می‌دهد (در لیست داکتر ویزیت بیاید)")
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(60)

        form.addRow("نام مکمل *", self.full_name)
        form.addRow("وظیفه", self.position)
        form.addRow("شماره تلفن", self.phone)
        form.addRow("نوع پرداخت", self.pay_type)
        form.addRow("معاش ماهانه", self.base_salary)
        form.addRow("فیصدی از معالجات", self.commission)
        form.addRow("", self.is_provider)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        if member:
            self.full_name.setText(member.get("full_name", ""))
            self.position.setCurrentText(member.get("position", ""))
            self.phone.setText(member.get("phone", ""))
            i = self.pay_type.findData(member.get("pay_type"))
            if i >= 0:
                self.pay_type.setCurrentIndex(i)
            self.base_salary.setValue(float(member.get("base_salary") or 0))
            self.commission.setValue(float(member.get("commission_pct") or 0))
            self.is_provider.setChecked(bool(member.get("is_provider")))
            self.notes.setPlainText(member.get("notes", ""))
        else:
            self.is_provider.setChecked(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        if not self.full_name.text().strip():
            QMessageBox.warning(self, "خطا", "نام مکمل الزامی است.")
            return
        provider = 1 if self.is_provider.isChecked() else 0
        if self.member:
            staff_model.update(
                self.member["id"], self.full_name.text(),
                self.position.currentText(), self.phone.text(),
                self.pay_type.currentData(), self.base_salary.value(),
                self.commission.value(), provider,
                self.member.get("is_active", 1), self.notes.toPlainText())
        else:
            staff_model.create(
                self.full_name.text(), self.position.currentText(),
                self.phone.text(), self.pay_type.currentData(),
                self.base_salary.value(), self.commission.value(),
                provider, self.notes.toPlainText())
        self.accept()


# ---------------------------------------------------------------------------
# Record a payout dialog
# ---------------------------------------------------------------------------

class StaffPaymentDialog(QDialog):
    def __init__(self, parent=None, staff_id: int = 0, suggested: float = 0):
        super().__init__(parent)
        self.staff_id = staff_id
        self.payment_id = None
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ثبت پرداخت به کارمند")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.kind = QComboBox()
        for key, label in staff_model.PAYMENT_KINDS.items():
            self.kind.addItem(label, key)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setSingleStep(500)
        self.amount.setGroupSeparatorShown(True)
        self.amount.setSuffix(" افغانی")
        if suggested > 0:
            self.amount.setValue(suggested)
        self.period = QLineEdit()
        self.period.setPlaceholderText("مثلاً حمل ۱۴۰۵")
        self.method = QComboBox()
        self.method.addItem("نقدی", "cash")
        self.method.addItem("انتقال بانکی", "bank")
        self.date = JalaliDateEdit()
        self.notes = QLineEdit()

        form.addRow("نوع پرداخت", self.kind)
        form.addRow("مبلغ *", self.amount)
        form.addRow("دوره", self.period)
        form.addRow("روش", self.method)
        form.addRow("تاریخ", self.date)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ثبت و رسید")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        if self.amount.value() <= 0:
            QMessageBox.warning(self, "خطا", "مبلغ باید بیشتر از صفر باشد.")
            return
        uid = session.current_user["id"] if session.current_user else None
        self.payment_id = staff_model.add_payment(
            self.staff_id, self.amount.value(), self.kind.currentData(),
            self.period.text(), self.method.currentData(),
            self.date.iso_date(), self.notes.text(), created_by=uid)
        self.accept()


# ---------------------------------------------------------------------------
# Staff detail (payroll account) dialog
# ---------------------------------------------------------------------------

def _mini(label: str, color: str):
    box = QFrame()
    box.setObjectName("Card")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(14, 12, 14, 12)
    val = QLabel("—")
    val.setStyleSheet(f"font-size:19px; font-weight:700; color:{color};")
    cap = QLabel(label)
    cap.setStyleSheet("color:#65788F; font-size:12px;")
    lay.addWidget(val)
    lay.addWidget(cap)
    return box, val


class StaffDetailDialog(QDialog):
    def __init__(self, parent=None, staff_id: int = 0):
        super().__init__(parent)
        self.staff_id = staff_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("حساب و پرداخت‌های کارمند")
        self.setMinimumSize(720, 560)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        member = staff_model.get(staff_id) or {}
        head = QHBoxLayout()
        name = QLabel(member.get("full_name", ""))
        name.setStyleSheet("font-size:20px; font-weight:700; color:#14253B;")
        pos = QLabel(member.get("position", ""))
        pos.setObjectName("Pill")
        head.addWidget(name)
        head.addWidget(pos)
        head.addStretch(1)
        add_btn = QPushButton("➕ ثبت پرداخت")
        add_btn.setObjectName("Success")
        add_btn.clicked.connect(self._add_payment)
        head.addWidget(add_btn)
        layout.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.box_treat, self.val_treat = _mini("مجموع معالجات", "#14253B")
        self.box_earn, self.val_earn = _mini("فیصدی کسب‌شده", "#0E9F8E")
        self.box_paid, self.val_paid = _mini("مجموع پرداخت‌شده", "#10A05B")
        self.box_bal, self.val_bal = _mini("باقیمانده فیصدی", "#E23D5B")
        for i, b in enumerate([self.box_treat, self.box_earn, self.box_paid, self.box_bal]):
            grid.addWidget(b, 0, i)
        layout.addLayout(grid)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["رسید", "تاریخ", "نوع", "دوره", "مبلغ", "روش", "عملیات"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        prepare_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table, 1)

        close_btn = QPushButton("بستن")
        close_btn.setObjectName("Secondary")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.refresh()

    def _add_payment(self):
        s = staff_model.summary(self.staff_id)
        dlg = StaffPaymentDialog(self, self.staff_id,
                                 suggested=max(s["commission_balance"], 0))
        if dlg.exec():
            self.refresh()
            if dlg.payment_id:
                self._print_receipt(dlg.payment_id)

    def _print_receipt(self, payment_id):
        html = printing.staff_receipt_html(payment_id)
        printing.print_or_pdf(self, html, "رسید پرداخت")

    def refresh(self):
        s = staff_model.summary(self.staff_id)
        self.val_treat.setText(helpers.format_money(s["treatments_total"]))
        self.val_earn.setText(helpers.format_money(s["commission_earned"]))
        self.val_paid.setText(helpers.format_money(s["total_paid"]))
        self.val_bal.setText(helpers.format_money(s["commission_balance"]))

        self.table.setRowCount(0)
        for p in staff_model.payments(self.staff_id):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_digits(p.get("receipt_no", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(
                helpers.jalali_date(p.get("pay_date"))))
            self.table.setItem(r, 2, QTableWidgetItem(
                staff_model.PAYMENT_KINDS.get(p.get("kind"), p.get("kind", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(p.get("period") or "—"))
            self.table.setItem(r, 4, QTableWidgetItem(
                helpers.format_money(p.get("amount", 0))))
            method = {"cash": "نقدی", "bank": "بانکی"}.get(
                p.get("method"), p.get("method", ""))
            self.table.setItem(r, 5, QTableWidgetItem(method))
            self.table.setCellWidget(r, 6, actions_cell([
                make_button("چاپ رسید", "primary", "چاپ رسید",
                            lambda pid=p["id"]: self._print_receipt(pid)),
                make_button("حذف", "danger", "حذف",
                            lambda pid=p["id"]: self._delete_payment(pid)),
            ]))

    def _delete_payment(self, pid):
        if QMessageBox.question(
            self, "حذف", "این پرداخت حذف شود؟"
        ) == QMessageBox.StandardButton.Yes:
            staff_model.delete_payment(pid)
            self.refresh()


# ---------------------------------------------------------------------------
# Main staff page
# ---------------------------------------------------------------------------

class StaffPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        bar = QHBoxLayout()
        hint = QLabel("ثبت داکتران و کارمندان کلینیک و مدیریت معاش و فیصدی آن‌ها")
        hint.setObjectName("SectionHint")
        bar.addWidget(hint)
        bar.addStretch(1)
        add_btn = QPushButton("➕ کارمند / داکتر جدید")
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self._add_staff)
        bar.addWidget(add_btn)
        layout.addLayout(bar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "نام", "وظیفه", "نوع پرداخت", "فیصدی کسب‌شده",
            "پرداخت‌شده", "باقیمانده", "وضعیت", "عملیات"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        prepare_table(self.table)
        self.table.doubleClicked.connect(self._open_selected)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def _add_staff(self):
        dlg = StaffDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit_staff(self, m):
        dlg = StaffDialog(self, member=m)
        if dlg.exec():
            self.refresh()

    def _open_detail(self, staff_id):
        dlg = StaffDetailDialog(self, staff_id=staff_id)
        dlg.exec()
        self.refresh()

    def _open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        sid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._open_detail(sid)

    def _delete_staff(self, m):
        if QMessageBox.question(
            self, "حذف", f"«{m['full_name']}» و تمام پرداخت‌هایش حذف شود؟"
        ) == QMessageBox.StandardButton.Yes:
            staff_model.delete(m["id"])
            self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        for m in staff_model.all_staff():
            s = staff_model.summary(m["id"])
            r = self.table.rowCount()
            self.table.insertRow(r)
            name_item = QTableWidgetItem(m.get("full_name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, m["id"])
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(m.get("position") or "—"))
            self.table.setItem(r, 2, QTableWidgetItem(
                staff_model.PAY_TYPES.get(m.get("pay_type"), "")))
            self.table.setItem(r, 3, QTableWidgetItem(
                helpers.format_money(s["commission_earned"])))
            self.table.setItem(r, 4, QTableWidgetItem(
                helpers.format_money(s["total_paid"])))
            bal_item = QTableWidgetItem(helpers.format_money(s["commission_balance"]))
            self.table.setItem(r, 5, bal_item)
            self.table.setItem(r, 6, QTableWidgetItem(
                "فعال" if m.get("is_active") else "غیرفعال"))

            self.table.setCellWidget(r, 7, actions_cell([
                make_button("حساب", "primary", "مشاهده حساب و ثبت پرداخت",
                            lambda sid=m["id"]: self._open_detail(sid)),
                make_button("ویرایش", "default", "ویرایش",
                            lambda mm=m: self._edit_staff(mm)),
                make_button("حذف", "danger", "حذف",
                            lambda mm=m: self._delete_staff(mm)),
            ]))
