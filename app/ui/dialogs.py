"""Modal dialogs for creating/editing core records."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget
)

from ..models import (
    attachment as attachment_model,
    payment as payment_model,
    treatment as treatment_model,
    user as user_model,
)
from ..models import patient as patient_model
from ..models import visit as visit_model
from ..services import session
from ..utils import helpers
from .widgets.jalali_date_edit import JalaliDateEdit


# ---------------------------------------------------------------------------
# Patient dialog
# ---------------------------------------------------------------------------

class PatientDialog(QDialog):
    def __init__(self, parent=None, patient: dict | None = None):
        super().__init__(parent)
        self.patient = patient
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ویرایش مریض" if patient else "ثبت مریض جدید")
        self.setMinimumWidth(420)
        self._build()
        if patient:
            self._load(patient)

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.full_name = QLineEdit()
        self.phone = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItem("مرد", "male")
        self.gender.addItem("زن", "female")
        self.age = QSpinBox()
        self.age.setRange(0, 130)
        self.address = QLineEdit()
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(70)

        form.addRow("نام مکمل *", self.full_name)
        form.addRow("شماره تلفن", self.phone)
        form.addRow("جنسیت", self.gender)
        form.addRow("سن", self.age)
        form.addRow("آدرس", self.address)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, p: dict):
        self.full_name.setText(p.get("full_name", ""))
        self.phone.setText(p.get("phone", ""))
        idx = self.gender.findData(p.get("gender"))
        if idx >= 0:
            self.gender.setCurrentIndex(idx)
        if p.get("age") is not None:
            self.age.setValue(int(p["age"]))
        self.address.setText(p.get("address", ""))
        self.notes.setPlainText(p.get("notes", ""))

    def _save(self):
        name = self.full_name.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام مریض الزامی است.")
            return
        age = self.age.value() or None
        if self.patient:
            patient_model.update(
                self.patient["id"], name, self.phone.text(),
                self.gender.currentData(), age, self.address.text(),
                self.notes.toPlainText(),
            )
            self.patient_id = self.patient["id"]
        else:
            self.patient_id = patient_model.create(
                name, self.phone.text(), self.gender.currentData(), age,
                self.address.text(), self.notes.toPlainText(),
            )
        self.accept()


# ---------------------------------------------------------------------------
# Visit dialog (with optional attachments)
# ---------------------------------------------------------------------------

class VisitDialog(QDialog):
    def __init__(self, parent=None, patient_id: int = 0, visit: dict | None = None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.visit = visit
        self._pending_files: list[str] = []
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ویرایش ویزیت" if visit else "ثبت ویزیت / معالجه")
        self.setMinimumWidth(460)
        self._build()
        if visit:
            self._load(visit)

    def _build(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.date = JalaliDateEdit()

        self.treatment = QComboBox()
        self.treatment.addItem("— انتخاب کنید —", None)
        for t in treatment_model.all_active():
            self.treatment.addItem(t["name"], t["id"])
        self.treatment.currentIndexChanged.connect(self._on_treatment_changed)

        self.tooth = QLineEdit()
        self.tooth.setPlaceholderText("مثلاً ۲۶")

        self.doctor = QComboBox()
        self.doctor.addItem("—", None)
        for d in user_model.doctors():
            self.doctor.addItem(d["full_name"] or d["username"], d["id"])
        # Preselect current user if they are a doctor
        if session.current_user:
            i = self.doctor.findData(session.current_user["id"])
            if i >= 0:
                self.doctor.setCurrentIndex(i)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 100_000_000)
        self.cost.setSingleStep(100)
        self.cost.setSuffix(" افغانی")
        self.cost.setGroupSeparatorShown(True)

        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(70)

        form.addRow("تاریخ ویزیت *", self.date)
        form.addRow("نوع معالجه", self.treatment)
        form.addRow("شماره دندان", self.tooth)
        form.addRow("داکتر", self.doctor)
        form.addRow("هزینه", self.cost)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        # Attachments section
        att_header = QHBoxLayout()
        att_header.addWidget(QLabel("ضمیمه‌ها (اختیاری)"))
        att_header.addStretch(1)
        add_file_btn = QPushButton("➕ افزودن فایل")
        add_file_btn.setObjectName("Secondary")
        add_file_btn.clicked.connect(self._add_files)
        att_header.addWidget(add_file_btn)
        layout.addLayout(att_header)

        self.att_list = QListWidget()
        self.att_list.setFixedHeight(110)
        layout.addWidget(self.att_list)

        remove_btn = QPushButton("حذف فایل انتخاب‌شده")
        remove_btn.setObjectName("Danger")
        remove_btn.clicked.connect(self._remove_selected_file)
        layout.addWidget(remove_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_treatment_changed(self):
        tid = self.treatment.currentData()
        if tid:
            t = treatment_model.get(tid)
            if t and self.cost.value() == 0:
                self.cost.setValue(float(t["default_price"]))

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "انتخاب فایل‌ها", "",
            "همه فایل‌ها (*.*);;تصاویر (*.png *.jpg *.jpeg);;PDF (*.pdf)"
        )
        for f in files:
            self._pending_files.append(f)
            item = QListWidgetItem("🆕 " + os.path.basename(f))
            item.setData(Qt.ItemDataRole.UserRole, ("pending", f))
            self.att_list.addItem(item)

    def _remove_selected_file(self):
        item = self.att_list.currentItem()
        if not item:
            return
        kind, ref = item.data(Qt.ItemDataRole.UserRole)
        if kind == "pending":
            self._pending_files.remove(ref)
        elif kind == "saved":
            if QMessageBox.question(
                self, "حذف", "این فایل به‌صورت دائمی حذف شود؟"
            ) == QMessageBox.StandardButton.Yes:
                attachment_model.delete(ref)
            else:
                return
        self.att_list.takeItem(self.att_list.row(item))

    def _load(self, v: dict):
        self.date.set_iso(v.get("visit_date"))
        i = self.treatment.findData(v.get("treatment_id"))
        if i >= 0:
            self.treatment.setCurrentIndex(i)
        elif v.get("treatment_name"):
            self.treatment.addItem(v["treatment_name"], None)
            self.treatment.setCurrentIndex(self.treatment.count() - 1)
        self.tooth.setText(v.get("tooth", ""))
        di = self.doctor.findData(v.get("doctor_id"))
        if di >= 0:
            self.doctor.setCurrentIndex(di)
        self.cost.setValue(float(v.get("cost", 0)))
        self.notes.setPlainText(v.get("notes", ""))
        for a in attachment_model.for_visit(v["id"]):
            item = QListWidgetItem("📎 " + (a.get("original_name") or ""))
            item.setData(Qt.ItemDataRole.UserRole, ("saved", a["id"]))
            self.att_list.addItem(item)

    def _save(self):
        iso = self.date.iso_date()
        if not iso:
            QMessageBox.warning(self, "خطا", "تاریخ ویزیت نامعتبر است.")
            return
        tname = self.treatment.currentText() if self.treatment.currentData() \
            or self.treatment.currentIndex() > 0 else ""
        if self.treatment.currentIndex() == 0:
            tname = ""
        doctor_name = self.doctor.currentText() if self.doctor.currentData() else ""

        if self.visit:
            visit_model.update(
                self.visit["id"], self.treatment.currentData(), tname,
                self.doctor.currentData(), doctor_name, iso,
                self.cost.value(), self.notes.toPlainText(), self.tooth.text(),
            )
            vid = self.visit["id"]
        else:
            vid = visit_model.create(
                self.patient_id, self.treatment.currentData(), tname,
                self.doctor.currentData(), doctor_name, iso,
                self.cost.value(), self.notes.toPlainText(), self.tooth.text(),
            )
        # Save pending attachments
        for f in self._pending_files:
            attachment_model.add(vid, self.patient_id, f)
        self.visit_id = vid
        self.accept()


# ---------------------------------------------------------------------------
# Payment dialog
# ---------------------------------------------------------------------------

class PaymentDialog(QDialog):
    def __init__(self, parent=None, patient_id: int = 0, balance: float = 0):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ثبت پرداخت")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)

        if balance > 0:
            info = QLabel("باقیمانده فعلی: " + helpers.format_money(balance))
            info.setStyleSheet("color:#dc2626; font-weight:bold;")
            layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setSingleStep(100)
        self.amount.setSuffix(" افغانی")
        self.amount.setGroupSeparatorShown(True)
        if balance > 0:
            self.amount.setValue(balance)
        self.method = QComboBox()
        self.method.addItem("نقدی", "cash")
        self.method.addItem("کارت / انتقال", "card")
        self.date = JalaliDateEdit()
        self.notes = QLineEdit()

        form.addRow("مبلغ پرداخت *", self.amount)
        form.addRow("روش پرداخت", self.method)
        form.addRow("تاریخ", self.date)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ثبت پرداخت")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        if self.amount.value() <= 0:
            QMessageBox.warning(self, "خطا", "مبلغ پرداخت باید بیشتر از صفر باشد.")
            return
        iso = self.date.iso_date()
        uid = session.current_user["id"] if session.current_user else None
        payment_model.create(
            self.patient_id, self.amount.value(), self.method.currentData(),
            iso, self.notes.text(), created_by=uid,
        )
        self.accept()
