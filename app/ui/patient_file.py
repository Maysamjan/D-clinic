"""Patient file page: profile, timeline, visits, payments, invoices, files."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget
)

from ..models import (
    attachment as attachment_model,
    invoice as invoice_model,
    patient as patient_model,
    payment as payment_model,
    visit as visit_model,
)
from ..services import session
from ..utils import helpers, printing
from .dialogs import PatientDialog, PaymentDialog, VisitDialog
from .invoice_dialog import InvoiceDialog
from .widgets.actions import actions_cell, make_button, prepare_table
from .widgets.timeline import TimelineWidget


def _summary_box(label: str, color: str) -> tuple[QFrame, QLabel]:
    box = QFrame()
    box.setObjectName("Card")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(14, 12, 14, 12)
    value = QLabel("—")
    value.setStyleSheet(f"font-size:20px; font-weight:bold; color:{color};")
    cap = QLabel(label)
    cap.setStyleSheet("color:#64748b; font-size:12px;")
    lay.addWidget(value)
    lay.addWidget(cap)
    return box, value


class PatientFilePage(QWidget):
    back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.patient_id: int | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 20, 26, 20)
        layout.setSpacing(16)

        # Top bar: back + name + actions
        top = QHBoxLayout()
        back_btn = QPushButton("→ بازگشت")
        back_btn.setObjectName("Secondary")
        back_btn.clicked.connect(self.back.emit)
        top.addWidget(back_btn)

        self.name_label = QLabel()
        self.name_label.setStyleSheet(
            "font-size:20px; font-weight:bold; color:#0f2942;")
        top.addWidget(self.name_label)
        self.code_label = QLabel()
        self.code_label.setStyleSheet(
            "background:#e8f0fe; color:#2563eb; padding:4px 10px; border-radius:8px;")
        top.addWidget(self.code_label)
        top.addStretch(1)

        self.edit_btn = QPushButton("✎ ویرایش")
        self.edit_btn.setObjectName("Secondary")
        self.edit_btn.clicked.connect(self._edit_patient)
        self.print_file_btn = QPushButton("🖨 چاپ پرونده")
        self.print_file_btn.clicked.connect(self._print_file)
        top.addWidget(self.edit_btn)
        top.addWidget(self.print_file_btn)
        layout.addLayout(top)

        # Summary cards
        grid = QGridLayout()
        grid.setSpacing(12)
        self.box_visits, self.val_visits = _summary_box("تعداد ویزیت", "#2563eb")
        self.box_cost, self.val_cost = _summary_box("مجموع هزینه", "#0f2942")
        self.box_paid, self.val_paid = _summary_box("پرداخت شده", "#16a34a")
        self.box_balance, self.val_balance = _summary_box("باقیمانده", "#dc2626")
        self.box_last, self.val_last = _summary_box("آخرین مراجعه", "#7c3aed")
        for i, b in enumerate([self.box_visits, self.box_cost, self.box_paid,
                               self.box_balance, self.box_last]):
            grid.addWidget(b, 0, i)
        layout.addLayout(grid)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_overview_tab()
        self._build_visits_tab()
        self._build_payments_tab()
        self._build_invoices_tab()
        self._build_files_tab()

        self._apply_permissions()

    # -- Tab builders -----------------------------------------------------
    def _build_overview_tab(self):
        tab = QWidget()
        lay = QHBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(14)

        # Personal info card
        info_card = QFrame()
        info_card.setObjectName("Card")
        info_card.setMaximumWidth(320)
        ilay = QVBoxLayout(info_card)
        ilay.setContentsMargins(16, 16, 16, 16)
        ilay.setSpacing(8)
        title = QLabel("معلومات شخصی")
        title.setObjectName("CardTitle")
        ilay.addWidget(title)
        self.info_labels: dict[str, QLabel] = {}
        for key, label in [
            ("phone", "تلفن"), ("gender", "جنسیت"), ("age", "سن"),
            ("address", "آدرس"), ("registered_at", "تاریخ ثبت"),
            ("notes", "یادداشت"),
        ]:
            row = QHBoxLayout()
            cap = QLabel(label + ":")
            cap.setStyleSheet("color:#64748b;")
            cap.setFixedWidth(80)
            val = QLabel("—")
            val.setWordWrap(True)
            val.setStyleSheet("font-weight:bold;")
            row.addWidget(cap)
            row.addWidget(val, 1)
            ilay.addLayout(row)
            self.info_labels[key] = val
        ilay.addStretch(1)
        lay.addWidget(info_card)

        # Timeline card
        tl_card = QFrame()
        tl_card.setObjectName("Card")
        tllay = QVBoxLayout(tl_card)
        tllay.setContentsMargins(16, 16, 16, 16)
        th = QHBoxLayout()
        tl_title = QLabel("📋 جدول زمانی مراجعات")
        tl_title.setObjectName("CardTitle")
        th.addWidget(tl_title)
        th.addStretch(1)
        self.add_visit_btn2 = QPushButton("➕ ویزیت جدید")
        self.add_visit_btn2.setObjectName("Success")
        self.add_visit_btn2.clicked.connect(self._add_visit)
        th.addWidget(self.add_visit_btn2)
        tllay.addLayout(th)
        self.timeline = TimelineWidget()
        tllay.addWidget(self.timeline, 1)
        lay.addWidget(tl_card, 1)

        self.tabs.addTab(tab, "نمای کلی و جدول زمانی")

    def _build_visits_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        bar = QHBoxLayout()
        self.add_visit_btn = QPushButton("➕ ثبت ویزیت")
        self.add_visit_btn.setObjectName("Success")
        self.add_visit_btn.clicked.connect(self._add_visit)
        bar.addWidget(self.add_visit_btn)
        bar.addStretch(1)
        lay.addLayout(bar)

        self.visits_table = QTableWidget(0, 7)
        self.visits_table.setHorizontalHeaderLabels([
            "تاریخ", "معالجه", "دندان", "داکتر", "هزینه", "یادداشت", "عملیات"])
        prepare_table(self.visits_table)
        self.visits_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.visits_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.visits_table.setAlternatingRowColors(True)
        h = self.visits_table.horizontalHeader()
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.visits_table)
        self.tabs.addTab(tab, "ویزیت‌ها / معالجات")

    def _build_payments_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        bar = QHBoxLayout()
        self.add_payment_btn = QPushButton("➕ ثبت پرداخت")
        self.add_payment_btn.setObjectName("Success")
        self.add_payment_btn.clicked.connect(self._add_payment)
        bar.addWidget(self.add_payment_btn)
        bar.addStretch(1)
        lay.addLayout(bar)

        self.payments_table = QTableWidget(0, 5)
        self.payments_table.setHorizontalHeaderLabels([
            "تاریخ", "مبلغ", "روش", "یادداشت", "عملیات"])
        prepare_table(self.payments_table)
        self.payments_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.payments_table.setAlternatingRowColors(True)
        h = self.payments_table.horizontalHeader()
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.payments_table)
        self.tabs.addTab(tab, "پرداخت‌ها")

    def _build_invoices_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        bar = QHBoxLayout()
        self.add_invoice_btn = QPushButton("➕ صدور صورتحساب")
        self.add_invoice_btn.setObjectName("Success")
        self.add_invoice_btn.clicked.connect(self._add_invoice)
        bar.addWidget(self.add_invoice_btn)
        bar.addStretch(1)
        lay.addLayout(bar)

        self.invoices_table = QTableWidget(0, 6)
        self.invoices_table.setHorizontalHeaderLabels([
            "شماره", "تاریخ", "مجموع", "پرداخت", "باقیمانده", "عملیات"])
        prepare_table(self.invoices_table)
        self.invoices_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.setAlternatingRowColors(True)
        h = self.invoices_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.invoices_table)
        self.tabs.addTab(tab, "صورتحساب‌ها")

    def _build_files_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        info = QLabel("برای افزودن فایل جدید، از داخل هر ویزیت استفاده کنید.")
        info.setStyleSheet("color:#64748b;")
        lay.addWidget(info)
        self.files_table = QTableWidget(0, 4)
        self.files_table.setHorizontalHeaderLabels(["نام فایل", "نوع", "تاریخ", "عملیات"])
        prepare_table(self.files_table)
        self.files_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.files_table.setAlternatingRowColors(True)
        h = self.files_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.files_table)
        self.tabs.addTab(tab, "فایل‌ها و تصاویر")

    # -- Permissions ------------------------------------------------------
    def _apply_permissions(self):
        can_visit = session.can("visit_add")
        self.add_visit_btn.setVisible(can_visit)
        self.add_visit_btn2.setVisible(can_visit)
        self.add_payment_btn.setVisible(session.can("payment_add"))
        self.add_invoice_btn.setVisible(session.can("invoices"))
        self.edit_btn.setVisible(session.can("patient_edit"))

    # -- Data loading -----------------------------------------------------
    def load_patient(self, patient_id: int):
        self.patient_id = patient_id
        self.refresh()

    def refresh(self):
        if self.patient_id is None:
            return
        p = patient_model.get(self.patient_id)
        if not p:
            self.back.emit()
            return
        self.name_label.setText(p.get("full_name", ""))
        self.code_label.setText(helpers.jalali_digits(p.get("code", "")))
        self.info_labels["phone"].setText(
            helpers.jalali_digits(p.get("phone")) or "—")
        self.info_labels["gender"].setText(helpers.gender_label(p.get("gender")))
        self.info_labels["age"].setText(
            helpers.jalali_digits(p.get("age")) if p.get("age") else "—")
        self.info_labels["address"].setText(p.get("address") or "—")
        self.info_labels["registered_at"].setText(
            helpers.jalali_date(p.get("registered_at")))
        self.info_labels["notes"].setText(p.get("notes") or "—")

        summary = patient_model.financial_summary(self.patient_id)
        self.val_visits.setText(helpers.jalali_digits(summary["visits"]))
        self.val_cost.setText(helpers.format_money(summary["total_cost"]))
        self.val_paid.setText(helpers.format_money(summary["total_paid"]))
        self.val_balance.setText(helpers.format_money(summary["balance"]))
        self.val_last.setText(
            helpers.jalali_date(summary["last_visit"]) if summary["last_visit"]
            else "—")

        visits = visit_model.for_patient(self.patient_id, ascending=True)
        self.timeline.set_visits(visits)
        self._fill_visits(visits)
        self._fill_payments()
        self._fill_invoices()
        self._fill_files()

    def _fill_visits(self, visits):
        self.visits_table.setRowCount(0)
        for v in reversed(visits):
            r = self.visits_table.rowCount()
            self.visits_table.insertRow(r)
            self.visits_table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_date(v.get("visit_date"))))
            self.visits_table.setItem(r, 1, QTableWidgetItem(
                v.get("treatment_name") or "ویزیت"))
            self.visits_table.setItem(r, 2, QTableWidgetItem(v.get("tooth") or "—"))
            self.visits_table.setItem(r, 3, QTableWidgetItem(
                v.get("doctor_name") or "—"))
            self.visits_table.setItem(r, 4, QTableWidgetItem(
                helpers.format_money(v.get("cost", 0))))
            self.visits_table.setItem(r, 5, QTableWidgetItem(v.get("notes") or ""))
            self.visits_table.setCellWidget(r, 6, self._visit_actions(v))

    def _visit_actions(self, v) -> QWidget:
        buttons = [make_button("چاپ", "primary", "چاپ ویزیت",
                               lambda vid=v["id"]: self._print_visit(vid))]
        if session.can("visit_add"):
            buttons.append(make_button("ویرایش", "default", "ویرایش ویزیت",
                                       lambda vv=v: self._edit_visit(vv)))
        if session.is_admin():
            buttons.append(make_button("حذف", "danger", "حذف ویزیت",
                                       lambda vid=v["id"]: self._delete_visit(vid)))
        return actions_cell(buttons)

    def _fill_payments(self):
        self.payments_table.setRowCount(0)
        for pay in payment_model.for_patient(self.patient_id):
            r = self.payments_table.rowCount()
            self.payments_table.insertRow(r)
            self.payments_table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_date(pay.get("pay_date"))))
            self.payments_table.setItem(r, 1, QTableWidgetItem(
                helpers.format_money(pay.get("amount", 0))))
            method = {"cash": "نقدی", "card": "کارت / انتقال"}.get(
                pay.get("method"), pay.get("method", ""))
            self.payments_table.setItem(r, 2, QTableWidgetItem(method))
            self.payments_table.setItem(r, 3, QTableWidgetItem(pay.get("notes") or ""))
            if session.is_admin():
                self.payments_table.setCellWidget(r, 4, actions_cell([
                    make_button("حذف", "danger", "حذف پرداخت",
                                lambda pid=pay["id"]: self._delete_payment(pid))]))

    def _fill_invoices(self):
        self.invoices_table.setRowCount(0)
        for inv in invoice_model.for_patient(self.patient_id):
            r = self.invoices_table.rowCount()
            self.invoices_table.insertRow(r)
            self.invoices_table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_digits(inv.get("number", ""))))
            self.invoices_table.setItem(r, 1, QTableWidgetItem(
                helpers.jalali_date(inv.get("issue_date"))))
            self.invoices_table.setItem(r, 2, QTableWidgetItem(
                helpers.format_money(inv.get("total", 0))))
            self.invoices_table.setItem(r, 3, QTableWidgetItem(
                helpers.format_money(inv.get("paid", 0))))
            bal = float(inv.get("total", 0)) - float(inv.get("paid", 0))
            self.invoices_table.setItem(r, 4, QTableWidgetItem(
                helpers.format_money(bal)))
            self.invoices_table.setCellWidget(r, 5, actions_cell([
                make_button("چاپ صورتحساب", "primary", "چاپ صورتحساب",
                            lambda iid=inv["id"]: self._print_invoice(iid))]))

    def _fill_files(self):
        self.files_table.setRowCount(0)
        for a in attachment_model.for_patient(self.patient_id):
            r = self.files_table.rowCount()
            self.files_table.insertRow(r)
            self.files_table.setItem(r, 0, QTableWidgetItem(
                a.get("original_name") or os.path.basename(a.get("file_path", ""))))
            ftype = {"image": "تصویر", "pdf": "PDF", "document": "سند"}.get(
                a.get("file_type"), a.get("file_type", ""))
            self.files_table.setItem(r, 1, QTableWidgetItem(ftype))
            self.files_table.setItem(r, 2, QTableWidgetItem(
                helpers.jalali_date(a.get("created_at"))))
            self.files_table.setCellWidget(r, 3, actions_cell([
                make_button("باز کردن", "primary", "باز کردن فایل",
                            lambda path=a.get("file_path"): self._open_file(path))]))

    # -- Actions ----------------------------------------------------------
    def _edit_patient(self):
        p = patient_model.get(self.patient_id)
        dlg = PatientDialog(self, patient=p)
        if dlg.exec():
            self.refresh()

    def _add_visit(self):
        dlg = VisitDialog(self, patient_id=self.patient_id)
        if dlg.exec():
            self.refresh()

    def _edit_visit(self, v):
        dlg = VisitDialog(self, patient_id=self.patient_id, visit=v)
        if dlg.exec():
            self.refresh()

    def _delete_visit(self, vid):
        if QMessageBox.question(
            self, "حذف ویزیت",
            "این ویزیت و ضمیمه‌های آن حذف شوند؟"
        ) == QMessageBox.StandardButton.Yes:
            visit_model.delete(vid)
            self.refresh()

    def _add_payment(self):
        summary = patient_model.financial_summary(self.patient_id)
        dlg = PaymentDialog(self, patient_id=self.patient_id,
                            balance=summary["balance"])
        if dlg.exec():
            self.refresh()

    def _delete_payment(self, pid):
        if QMessageBox.question(
            self, "حذف پرداخت", "این پرداخت حذف شود؟"
        ) == QMessageBox.StandardButton.Yes:
            payment_model.delete(pid)
            self.refresh()

    def _add_invoice(self):
        dlg = InvoiceDialog(self, patient_id=self.patient_id)
        if dlg.exec():
            self.refresh()
            if getattr(dlg, "invoice_id", None):
                self._print_invoice(dlg.invoice_id)

    def _open_file(self, path):
        if path and os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "خطا", "فایل یافت نشد.")

    # -- Printing ---------------------------------------------------------
    def _print_file(self):
        html = printing.patient_file_html(self.patient_id)
        self._print_or_pdf(html, "پرونده مریض")

    def _print_visit(self, vid):
        html = printing.visit_html(vid)
        self._print_or_pdf(html, "ویزیت")

    def _print_invoice(self, iid):
        html = printing.invoice_html(iid)
        self._print_or_pdf(html, "صورتحساب")

    def _print_or_pdf(self, html, title):
        printing.print_or_pdf(self, html, title)
