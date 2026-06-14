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
    staff as staff_model,
    treatment as treatment_model,
)
from ..models import patient as patient_model
from ..models import visit as visit_model
from ..services import session
from ..utils import helpers
from ..services.i18n import t
from .widgets.dialog_header import setup_form_dialog
from .widgets.jalali_date_edit import JalaliDateEdit


# ---------------------------------------------------------------------------
# Patient dialog
# ---------------------------------------------------------------------------

class PatientDialog(QDialog):
    def __init__(self, parent=None, patient: dict | None = None):
        super().__init__(parent)
        self.patient = patient
        self.setWindowTitle("ویرایش مریض" if patient else "ثبت مریض جدید")
        self.setMinimumWidth(440)
        self._build()
        if patient:
            self._load(patient)

    def _build(self):
        sub = (f"کود: {helpers.jalali_digits(self.patient.get('code',''))}"
               if self.patient else "اطلاعات مریض جدید را وارد کنید")
        layout = setup_form_dialog(
            self, "ویرایش مریض" if self.patient else "ثبت مریض جدید", sub, "👤")
        form = QFormLayout()
        form.setSpacing(13)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.full_name = QLineEdit()
        self.phone = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItem(t("مرد"), "male")
        self.gender.addItem(t("زن"), "female")
        self.age = QSpinBox()
        self.age.setRange(0, 130)
        self.address = QLineEdit()
        self.blood_type = QComboBox()
        self.blood_type.addItem("—", "")
        for bt in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]:
            self.blood_type.addItem(bt, bt)
        self.allergies = QLineEdit()
        self.allergies.setPlaceholderText(t("مثلاً حساسیت به پنسلین (در صورت وجود)"))
        self.medical_history = QPlainTextEdit()
        self.medical_history.setFixedHeight(52)
        self.medical_history.setPlaceholderText(t("بیماری‌های زمینه‌ای: فشار خون، دیابت، قلبی ..."))
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(52)

        form.addRow(t("نام مکمل *"), self.full_name)
        form.addRow(t("شماره تلفن"), self.phone)
        form.addRow(t("جنسیت"), self.gender)
        form.addRow(t("سن"), self.age)
        form.addRow(t("آدرس"), self.address)
        form.addRow(t("گروه خون"), self.blood_type)
        form.addRow(t("⚠ حساسیت‌ها"), self.allergies)
        form.addRow(t("سوابق طبی"), self.medical_history)
        form.addRow(t("یادداشت"), self.notes)
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
        bi = self.blood_type.findData(p.get("blood_type") or "")
        if bi >= 0:
            self.blood_type.setCurrentIndex(bi)
        self.allergies.setText(p.get("allergies", "") or "")
        self.medical_history.setPlainText(p.get("medical_history", "") or "")
        self.notes.setPlainText(p.get("notes", ""))

    def _save(self):
        name = self.full_name.text().strip()
        if not name:
            QMessageBox.warning(self, t("خطا"), t("نام مریض الزامی است."))
            return
        age = self.age.value() or None
        if self.patient:
            patient_model.update(
                self.patient["id"], name, self.phone.text(),
                self.gender.currentData(), age, self.address.text(),
                self.notes.toPlainText(), allergies=self.allergies.text(),
                medical_history=self.medical_history.toPlainText(),
                blood_type=self.blood_type.currentData(),
            )
            self.patient_id = self.patient["id"]
        else:
            self.patient_id = patient_model.create(
                name, self.phone.text(), self.gender.currentData(), age,
                self.address.text(), self.notes.toPlainText(),
                allergies=self.allergies.text(),
                medical_history=self.medical_history.toPlainText(),
                blood_type=self.blood_type.currentData(),
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
        self.setWindowTitle("ویرایش ویزیت" if visit else "ثبت ویزیت / معالجه")
        self.setMinimumWidth(460)
        self._build()
        if visit:
            self._load(visit)

    def _build(self):
        layout = setup_form_dialog(
            self, "ویرایش ویزیت" if self.visit else "ثبت ویزیت / معالجه",
            "جزئیات معالجه و هزینه را وارد کنید", "🦷")
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.date = JalaliDateEdit()

        self.treatment = QComboBox()
        self.treatment.addItem(t("— انتخاب کنید —"), None)
        for tr in treatment_model.all_active():
            self.treatment.addItem(tr["name"], tr["id"])
        self.treatment.currentIndexChanged.connect(self._on_treatment_changed)

        self.tooth = QLineEdit()
        self.tooth.setPlaceholderText(t("مثلاً ۲۶"))

        # Treatment provider — pulled from the staff registry so the visit
        # can be attributed for commission/payroll.
        self.doctor = QComboBox()
        self.doctor.addItem("—", None)
        for d in staff_model.providers():
            self.doctor.addItem(d["full_name"], d["id"])

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 100_000_000)
        self.cost.setSingleStep(100)
        self.cost.setSuffix(" افغانی")
        self.cost.setGroupSeparatorShown(True)

        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(70)

        # Optional follow-up / recall date (empty by default).
        self.next_visit = JalaliDateEdit(default_today=False, clearable=True)

        form.addRow(t("تاریخ ویزیت *"), self.date)
        form.addRow(t("نوع معالجه"), self.treatment)
        form.addRow(t("شماره دندان"), self.tooth)
        form.addRow(t("داکتر"), self.doctor)
        form.addRow(t("هزینه"), self.cost)
        form.addRow(t("یادداشت"), self.notes)
        form.addRow(t("مراجعه بعدی (اختیاری)"), self.next_visit)
        layout.addLayout(form)

        # Attachments section
        att_header = QHBoxLayout()
        att_header.addWidget(QLabel(t("ضمیمه‌ها (اختیاری)")))
        att_header.addStretch(1)
        add_file_btn = QPushButton(t("➕ افزودن فایل"))
        add_file_btn.setObjectName("Secondary")
        add_file_btn.clicked.connect(self._add_files)
        att_header.addWidget(add_file_btn)
        layout.addLayout(att_header)

        self.att_list = QListWidget()
        self.att_list.setFixedHeight(110)
        layout.addWidget(self.att_list)

        remove_btn = QPushButton(t("حذف فایل انتخاب‌شده"))
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
            tr = treatment_model.get(tid)
            if tr and self.cost.value() == 0:
                self.cost.setValue(float(tr["default_price"]))

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
                self, t("حذف"), t("این فایل به‌صورت دائمی حذف شود؟")
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
        di = self.doctor.findData(v.get("staff_id"))
        if di >= 0:
            self.doctor.setCurrentIndex(di)
        elif v.get("doctor_name"):
            # legacy visit whose provider is not in the staff list
            self.doctor.addItem(v["doctor_name"], None)
            self.doctor.setCurrentIndex(self.doctor.count() - 1)
        self.cost.setValue(float(v.get("cost", 0)))
        self.notes.setPlainText(v.get("notes", ""))
        if v.get("next_visit_date"):
            self.next_visit.set_iso(v.get("next_visit_date"))
        for a in attachment_model.for_visit(v["id"]):
            item = QListWidgetItem("📎 " + (a.get("original_name") or ""))
            item.setData(Qt.ItemDataRole.UserRole, ("saved", a["id"]))
            self.att_list.addItem(item)

    def _save(self):
        iso = self.date.iso_date()
        if not iso:
            QMessageBox.warning(self, t("خطا"), t("تاریخ ویزیت نامعتبر است."))
            return
        tname = self.treatment.currentText() if self.treatment.currentData() \
            or self.treatment.currentIndex() > 0 else ""
        if self.treatment.currentIndex() == 0:
            tname = ""
        staff_id = self.doctor.currentData()
        doctor_name = self.doctor.currentText() if self.doctor.currentIndex() > 0 else ""

        next_iso = self.next_visit.iso_date()
        if self.visit:
            visit_model.update(
                self.visit["id"], self.treatment.currentData(), tname,
                None, doctor_name, iso, self.cost.value(),
                self.notes.toPlainText(), self.tooth.text(), staff_id=staff_id,
                next_visit_date=next_iso,
            )
            vid = self.visit["id"]
        else:
            vid = visit_model.create(
                self.patient_id, self.treatment.currentData(), tname,
                None, doctor_name, iso, self.cost.value(),
                self.notes.toPlainText(), self.tooth.text(), staff_id=staff_id,
                next_visit_date=next_iso,
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
        self.setWindowTitle(t("ثبت پرداخت"))
        self.setMinimumWidth(400)
        sub = ("باقیمانده فعلی: " + helpers.format_money(balance)
               if balance > 0 else "ثبت پرداخت مریض")
        layout = setup_form_dialog(self, "ثبت پرداخت", sub, "💳")

        form = QFormLayout()
        form.setSpacing(13)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setSingleStep(100)
        self.amount.setSuffix(" افغانی")
        self.amount.setGroupSeparatorShown(True)
        if balance > 0:
            self.amount.setValue(balance)
        self.method = QComboBox()
        self.method.addItem(t("نقدی"), "cash")
        self.method.addItem(t("کارت / انتقال"), "card")
        self.date = JalaliDateEdit()
        self.notes = QLineEdit()

        form.addRow(t("مبلغ پرداخت *"), self.amount)
        form.addRow(t("روش پرداخت"), self.method)
        form.addRow(t("تاریخ"), self.date)
        form.addRow(t("یادداشت"), self.notes)
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
            QMessageBox.warning(self, t("خطا"), t("مبلغ پرداخت باید بیشتر از صفر باشد."))
            return
        iso = self.date.iso_date()
        uid = session.current_user["id"] if session.current_user else None
        payment_model.create(
            self.patient_id, self.amount.value(), self.method.currentData(),
            iso, self.notes.text(), created_by=uid,
        )
        self.accept()


# ---------------------------------------------------------------------------
# Treatment plan dialog
# ---------------------------------------------------------------------------

class TreatmentPlanDialog(QDialog):
    def __init__(self, parent=None, patient_id: int = 0, plan: dict | None = None):
        super().__init__(parent)
        from ..models import treatment_plan as plan_model
        self._plan_model = plan_model
        self.patient_id = patient_id
        self.plan = plan
        self.setWindowTitle(t("ویرایش پلان معالجه") if plan
                            else t("افزودن به پلان معالجه"))
        self.setMinimumWidth(440)
        layout = setup_form_dialog(
            self, t("ویرایش پلان معالجه") if plan else t("پلان معالجه"),
            "معالجه‌ی برنامه‌ریزی‌شده برای آینده", "📝")
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.treatment = QComboBox()
        self.treatment.setEditable(True)
        for tr in treatment_model.all_active():
            self.treatment.addItem(tr["name"], tr["id"])
        self.treatment.setCurrentText("")
        self.treatment.currentIndexChanged.connect(self._on_treatment_changed)

        self.tooth = QLineEdit()
        self.tooth.setPlaceholderText(t("مثلاً ۲۶"))
        self.est_cost = QDoubleSpinBox()
        self.est_cost.setRange(0, 100_000_000)
        self.est_cost.setSingleStep(100)
        self.est_cost.setSuffix(" افغانی")
        self.est_cost.setGroupSeparatorShown(True)
        self.status = QComboBox()
        for key, label in self._plan_model.STATUSES.items():
            self.status.addItem(t(label), key)
        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(60)

        form.addRow(t("معالجه *"), self.treatment)
        form.addRow(t("شماره دندان"), self.tooth)
        form.addRow(t("هزینه تخمینی"), self.est_cost)
        form.addRow(t("وضعیت"), self.status)
        form.addRow(t("یادداشت"), self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(t("ذخیره"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("لغو"))
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if plan:
            self._load(plan)

    def _on_treatment_changed(self):
        tid = self.treatment.currentData()
        if tid:
            tr = treatment_model.get(tid)
            if tr and self.est_cost.value() == 0:
                self.est_cost.setValue(float(tr["default_price"]))

    def _load(self, plan: dict):
        self.treatment.setCurrentText(plan.get("treatment", ""))
        self.tooth.setText(plan.get("tooth", "") or "")
        self.est_cost.setValue(float(plan.get("est_cost", 0)))
        si = self.status.findData(plan.get("status", "planned"))
        if si >= 0:
            self.status.setCurrentIndex(si)
        self.notes.setPlainText(plan.get("notes", "") or "")

    def _save(self):
        treatment = self.treatment.currentText().strip()
        if not treatment:
            QMessageBox.warning(self, t("خطا"), t("نام معالجه الزامی است."))
            return
        if self.plan:
            self._plan_model.update(
                self.plan["id"], treatment, self.tooth.text().strip(),
                self.est_cost.value(), self.status.currentData(),
                self.notes.toPlainText())
        else:
            self._plan_model.create(
                self.patient_id, treatment, self.tooth.text().strip(),
                self.est_cost.value(), self.status.currentData(),
                self.notes.toPlainText())
        self.accept()
