"""Prescription creation dialog (drug list) for a patient."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout
)

from ..models import prescription as presc_model
from ..models import staff as staff_model
from ..services import session
from ..services.i18n import t
from .widgets.dialog_header import setup_form_dialog

COMMON_DRUGS = [
    "اموکسی‌سیلین ۵۰۰mg", "مترونیدازول ۲۵۰mg", "آیبوپروفن ۴۰۰mg",
    "پاراستامول ۵۰۰mg", "دیکلوفناک", "کلیندامایسین ۳۰۰mg",
    "کلرهگزیدین (دهان‌شویه)", "آموکسی‌کلاو",
]


class PrescriptionDialog(QDialog):
    def __init__(self, parent=None, patient_id: int = 0,
                 prescription: dict | None = None):
        super().__init__(parent)
        self.patient_id = patient_id or (prescription or {}).get("patient_id", 0)
        self.prescription = prescription
        self.prescription_id = prescription["id"] if prescription else None
        is_edit = prescription is not None
        self.setWindowTitle(t("ویرایش نسخه") if is_edit else t("نسخه‌ی جدید"))
        self.setMinimumWidth(620)
        layout = setup_form_dialog(
            self, "ویرایش نسخه" if is_edit else "نسخه‌ی جدید",
            "تجویز دوا برای مریض", "℞")

        drow = QHBoxLayout()
        from PyQt6.QtWidgets import QLabel
        drow.addWidget(QLabel(t("داکتر") + ":"))
        self.doctor = QComboBox()
        self.doctor.setEditable(True)
        for d in staff_model.providers():
            self.doctor.addItem(d["full_name"], d["id"])
        if is_edit:
            self.doctor.setCurrentText(prescription.get("doctor_name", ""))
        elif session.current_user:
            self.doctor.setCurrentText(session.current_user.get("full_name", ""))
        drow.addWidget(self.doctor, 1)
        layout.addLayout(drow)

        # add-drug row
        add_row = QHBoxLayout()
        self.drug = QComboBox()
        self.drug.setEditable(True)
        self.drug.addItem("")
        self.drug.addItems(COMMON_DRUGS)
        self.dosage = QLineEdit()
        self.dosage.setPlaceholderText(t("مقدار مصرف، مثلاً ۱ قرص"))
        self.quantity = QLineEdit()
        self.quantity.setPlaceholderText(t("تعداد تحویلی، مثلاً ۲۰ عدد یا ۲ تخته"))
        self.instr = QLineEdit()
        self.instr.setPlaceholderText(t("دستور، مثلاً هر ۸ ساعت بعد از غذا"))
        add_btn = QPushButton(t("افزودن"))
        add_btn.setObjectName("Success")
        add_btn.clicked.connect(self._add_item)
        add_row.addWidget(self.drug, 2)
        add_row.addWidget(self.dosage, 1)
        add_row.addWidget(self.quantity, 1)
        add_row.addWidget(self.instr, 2)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([t("دوا"), t("مقدار مصرف"), t("تعداد تحویلی"), t("دستور مصرف"), ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(
            3, self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.setColumnWidth(4, 52)
        layout.addWidget(self.table)

        self.notes = QLineEdit()
        self.notes.setPlaceholderText(t("یادداشت (اختیاری)"))
        layout.addWidget(self.notes)

        # Load existing items when editing
        if is_edit:
            self.notes.setText(prescription.get("notes", ""))
            for it in presc_model.items(prescription["id"]):
                self._insert_row(it.get("drug", ""), it.get("dosage", ""),
                                 it.get("quantity", ""), it.get("instructions", ""))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(
            t("ذخیره") if is_edit else t("صدور و چاپ"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("لغو"))
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _insert_row(self, drug, dosage, quantity, instr):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(drug))
        self.table.setItem(r, 1, QTableWidgetItem(dosage))
        self.table.setItem(r, 2, QTableWidgetItem(quantity))
        self.table.setItem(r, 3, QTableWidgetItem(instr))
        rm = QPushButton("✕")
        rm.setObjectName("Danger")
        rm.setFixedWidth(40)
        rm.clicked.connect(
            lambda _, row_item=self.table.item(r, 0): self._remove(row_item))
        self.table.setCellWidget(r, 4, rm)

    def _add_item(self):
        drug = self.drug.currentText().strip()
        if not drug:
            QMessageBox.warning(self, t("خطا"), t("نام دوا را وارد کنید."))
            return
        self._insert_row(drug, self.dosage.text(), self.quantity.text(),
                         self.instr.text())
        self.drug.setCurrentText("")
        self.dosage.clear()
        self.quantity.clear()
        self.instr.clear()

    def _remove(self, item):
        self.table.removeRow(item.row())

    def _items(self):
        out = []
        for r in range(self.table.rowCount()):
            out.append((self.table.item(r, 0).text(),
                        self.table.item(r, 1).text(),
                        self.table.item(r, 2).text(),
                        self.table.item(r, 3).text()))
        return out

    def _save(self):
        items = self._items()
        if not items:
            QMessageBox.warning(self, t("خطا"), t("حداقل یک دوا اضافه کنید."))
            return
        uid = session.current_user["id"] if session.current_user else None
        if self.prescription:
            presc_model.update(self.prescription["id"], self.doctor.currentText(),
                               items, notes=self.notes.text())
            self.prescription_id = self.prescription["id"]
        else:
            self.prescription_id = presc_model.create(
                self.patient_id, self.doctor.currentText(), items,
                notes=self.notes.text(), created_by=uid)
        self.accept()
