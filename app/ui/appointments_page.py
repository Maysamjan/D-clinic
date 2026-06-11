"""Appointments / scheduling page (offline calendar by day)."""

from __future__ import annotations

import datetime

from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget
)

from ..models import appointment as appt_model
from ..models import patient as patient_model
from ..models import staff as staff_model
from ..services import jalali
from ..utils import helpers
from .widgets.actions import actions_cell, make_button, prepare_table
from .widgets.dialog_header import setup_form_dialog
from .widgets.jalali_date_edit import JalaliDateEdit

_STATUS_COLORS = {
    "scheduled": "#2563EB",
    "done": "#0C7A43",
    "cancelled": "#94A3B8",
    "noshow": "#E11D48",
}


class AppointmentDialog(QDialog):
    def __init__(self, parent=None, appt: dict | None = None,
                 date_iso: str | None = None):
        super().__init__(parent)
        self.appt = appt
        self.setWindowTitle("ویرایش نوبت" if appt else "ثبت نوبت جدید")
        self.setMinimumWidth(440)
        layout = setup_form_dialog(
            self, "ویرایش نوبت" if appt else "ثبت نوبت جدید",
            "تعیین وقت ملاقات مریض", "🗓")
        form = QFormLayout()
        form.setSpacing(13)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.patient = QComboBox()
        self.patient.setEditable(True)
        self.patient.addItem("— مریض جدید / مراجعه‌کننده —", None)
        for p in patient_model.search("", limit=1000):
            label = p["full_name"] + (" — " + helpers.jalali_digits(p["phone"])
                                      if p.get("phone") else "")
            self.patient.addItem(label, p["id"])
        self.patient.currentIndexChanged.connect(self._on_patient)

        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.date = JalaliDateEdit()
        if date_iso:
            self.date.set_iso(date_iso)
        self.time = QTimeEdit()
        self.time.setDisplayFormat("HH:mm")
        self.time.setTime(QTime(10, 0))
        self.doctor = QComboBox()
        self.doctor.addItem("—", None)
        for d in staff_model.providers():
            self.doctor.addItem(d["full_name"], d["id"])
        self.reason = QLineEdit()
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(50)

        form.addRow("مریض", self.patient)
        form.addRow("نام (در صورت جدید)", self.name)
        form.addRow("تلفن", self.phone)
        form.addRow("تاریخ *", self.date)
        form.addRow("ساعت", self.time)
        form.addRow("داکتر", self.doctor)
        form.addRow("علت مراجعه", self.reason)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        if appt:
            self._load(appt)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_patient(self):
        pid = self.patient.currentData()
        if pid:
            p = patient_model.get(pid)
            if p:
                self.name.setText(p.get("full_name", ""))
                self.phone.setText(p.get("phone", ""))

    def _load(self, a):
        if a.get("patient_id"):
            i = self.patient.findData(a["patient_id"])
            if i >= 0:
                self.patient.setCurrentIndex(i)
        self.name.setText(a.get("patient_name", ""))
        self.phone.setText(a.get("phone", ""))
        self.date.set_iso(a.get("appt_date"))
        if a.get("appt_time"):
            try:
                hh, mm = a["appt_time"].split(":")
                self.time.setTime(QTime(int(hh), int(mm)))
            except (ValueError, IndexError):
                pass
        di = self.doctor.findData(a.get("staff_id"))
        if di >= 0:
            self.doctor.setCurrentIndex(di)
        self.reason.setText(a.get("reason", ""))
        self.notes.setPlainText(a.get("notes", ""))

    def _save(self):
        iso = self.date.iso_date()
        if not iso:
            QMessageBox.warning(self, "خطا", "تاریخ نامعتبر است.")
            return
        pid = self.patient.currentData()
        name = self.name.text().strip() or self.patient.currentText()
        if not name:
            QMessageBox.warning(self, "خطا", "نام مریض را وارد کنید.")
            return
        staff_id = self.doctor.currentData()
        doctor_name = self.doctor.currentText() if staff_id else ""
        time_str = self.time.time().toString("HH:mm")
        if self.appt:
            appt_model.update(
                self.appt["id"], pid, name, self.phone.text(), staff_id,
                doctor_name, iso, time_str, self.reason.text(),
                self.notes.toPlainText())
        else:
            appt_model.create(
                pid, name, self.phone.text(), staff_id, doctor_name, iso,
                time_str, self.reason.text(), self.notes.toPlainText())
        self.accept()


class AppointmentsPage(QWidget):
    open_patient = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date = datetime.date.today()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        prev_btn = QPushButton("‹ روز قبل")
        prev_btn.setObjectName("Secondary")
        prev_btn.clicked.connect(lambda: self._shift(-1))
        next_btn = QPushButton("روز بعد ›")
        next_btn.setObjectName("Secondary")
        next_btn.clicked.connect(lambda: self._shift(1))
        today_btn = QPushButton("امروز")
        today_btn.setObjectName("Secondary")
        today_btn.clicked.connect(self._go_today)
        self.date_label = QLabel()
        self.date_label.setStyleSheet(
            "font-size:17px; font-weight:700; color:#0E9F8E;")
        bar.addWidget(prev_btn)
        bar.addWidget(today_btn)
        bar.addWidget(next_btn)
        bar.addWidget(self.date_label, 1, Qt.AlignmentFlag.AlignCenter)
        add_btn = QPushButton("➕ نوبت جدید")
        add_btn.setMinimumHeight(42)
        add_btn.clicked.connect(self._add)
        bar.addWidget(add_btn)
        layout.addLayout(bar)

        self.count_label = QLabel()
        self.count_label.setObjectName("SectionHint")
        layout.addWidget(self.count_label)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ساعت", "مریض", "تلفن", "داکتر", "علت مراجعه", "وضعیت", "عملیات"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        prepare_table(self.table)
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        h = self.table.horizontalHeader()
        h.setMinimumSectionSize(70)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def _shift(self, days):
        self._date += datetime.timedelta(days=days)
        self.refresh()

    def _go_today(self):
        self._date = datetime.date.today()
        self.refresh()

    def _add(self):
        dlg = AppointmentDialog(self, date_iso=self._date.isoformat())
        if dlg.exec():
            self.refresh()

    def _edit(self, a):
        dlg = AppointmentDialog(self, appt=a)
        if dlg.exec():
            self.refresh()

    def _set_status(self, aid, status):
        appt_model.set_status(aid, status)
        self.refresh()

    def _delete(self, aid):
        if QMessageBox.question(
            self, "حذف", "این نوبت حذف شود؟"
        ) == QMessageBox.StandardButton.Yes:
            appt_model.delete(aid)
            self.refresh()

    def refresh(self):
        iso = self._date.isoformat()
        self.date_label.setText("📅  " + jalali.long_jalali(iso))
        appts = appt_model.for_date(iso)
        self.count_label.setText(
            f"{helpers.jalali_digits(len(appts))} نوبت در این روز")
        self.table.setRowCount(0)
        for a in appts:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_digits(a.get("appt_time", "")) or "—"))
            self.table.setItem(r, 1, QTableWidgetItem(a.get("patient_name", "")))
            self.table.setItem(r, 2, QTableWidgetItem(
                helpers.jalali_digits(a.get("phone", "")) or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(a.get("doctor_name") or "—"))
            self.table.setItem(r, 4, QTableWidgetItem(a.get("reason") or "—"))
            st = QTableWidgetItem(appt_model.STATUSES.get(
                a.get("status"), a.get("status", "")))
            st.setForeground(QColor(_STATUS_COLORS.get(a.get("status"), "#334155")))
            self.table.setItem(r, 5, st)
            self.table.setCellWidget(r, 6, self._actions(a))

    def _actions(self, a):
        buttons = []
        if a.get("status") == "scheduled":
            buttons.append(make_button("انجام", "success", "انجام‌شده",
                                       lambda aid=a["id"]: self._set_status(aid, "done")))
            buttons.append(make_button("لغو", "warn", "لغو نوبت",
                                       lambda aid=a["id"]: self._set_status(aid, "cancelled")))
        if a.get("patient_id"):
            buttons.append(make_button("پرونده", "primary", "باز کردن پرونده",
                                       lambda pid=a["patient_id"]: self.open_patient.emit(pid)))
        buttons.append(make_button("ویرایش", "default", "ویرایش",
                                   lambda aa=a: self._edit(aa)))
        buttons.append(make_button("حذف", "danger", "حذف",
                                   lambda aid=a["id"]: self._delete(aid)))
        return actions_cell(buttons)
