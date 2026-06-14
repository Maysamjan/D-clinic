"""Patients list with fast search."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from ..models import patient as patient_model
from ..services import session
from ..utils import helpers
from ..services.i18n import t
from .dialogs import PatientDialog
from .widgets.actions import actions_cell, make_button, prepare_table


class PatientsPage(QWidget):
    open_patient = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        # Search + actions bar
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("🔍  جستجو با نام، شماره تلفن یا کود مریض ..."))
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)

        self.add_btn = QPushButton(t("➕ مریض جدید"))
        self.add_btn.setMinimumHeight(42)
        self.add_btn.clicked.connect(self._add_patient)
        bar.addWidget(self.add_btn)
        layout.addLayout(bar)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("color:#64748b;")
        layout.addWidget(self.count_label)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            t("کود"), t("نام مکمل"), t("تلفن"), t("جنسیت"), t("سن"), t("تاریخ ثبت"), t("عملیات")
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        prepare_table(self.table)
        self.table.doubleClicked.connect(self._open_selected)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in (0, 2, 3, 4, 5, 6):
            header.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        if not session.can("patient_add"):
            self.add_btn.hide()

    def _add_patient(self):
        dlg = PatientDialog(self)
        if dlg.exec():
            self.refresh()
            self.open_patient.emit(dlg.patient_id)

    def _open_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.open_patient.emit(pid)

    def refresh(self):
        term = self.search.text()
        patients = patient_model.search(term)
        self.count_label.setText(
            helpers.jalali_digits(len(patients)) + " " + t("مریض یافت شد"))
        self.table.setRowCount(0)
        for p in patients:
            r = self.table.rowCount()
            self.table.insertRow(r)
            code_item = QTableWidgetItem(helpers.jalali_digits(p.get("code", "")))
            code_item.setData(Qt.ItemDataRole.UserRole, p["id"])
            self.table.setItem(r, 0, code_item)
            self.table.setItem(r, 1, QTableWidgetItem(p.get("full_name", "")))
            self.table.setItem(r, 2, QTableWidgetItem(
                helpers.jalali_digits(p.get("phone", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(
                helpers.gender_label(p.get("gender", ""))))
            self.table.setItem(r, 4, QTableWidgetItem(
                helpers.jalali_digits(p.get("age")) if p.get("age") else "—"))
            self.table.setItem(r, 5, QTableWidgetItem(
                helpers.jalali_date(p.get("registered_at"))))

            self.table.setCellWidget(r, 6, actions_cell([
                make_button("باز کردن پرونده", "primary", "باز کردن پرونده",
                            lambda pid=p["id"]: self.open_patient.emit(pid))]))
