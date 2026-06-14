"""Service pricing and treatment-type management (admin)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget
)

from ..models import service_price as service_model
from ..models import treatment as treatment_model
from ..utils import helpers
from ..services.i18n import t
from .widgets.actions import actions_cell, make_button, prepare_table


class _PriceDialog(QDialog):
    def __init__(self, parent=None, title="افزودن", name="", price=0.0):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(name)
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 100_000_000)
        self.price.setSingleStep(100)
        self.price.setGroupSeparatorShown(True)
        self.price.setSuffix(" افغانی")
        self.price.setValue(float(price))
        form.addRow(t("نام *"), self.name)
        form.addRow(t("قیمت"), self.price)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, t("خطا"), t("نام الزامی است."))
            return
        self.accept()


class ServicesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        tabs.addTab(self._build_services_tab(), t("لیست قیمت خدمات"))
        tabs.addTab(self._build_treatments_tab(), t("انواع معالجه"))

    # -- Services ---------------------------------------------------------
    def _build_services_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        bar = QHBoxLayout()
        add_btn = QPushButton(t("➕ خدمت جدید"))
        add_btn.clicked.connect(self._add_service)
        bar.addWidget(add_btn)
        bar.addStretch(1)
        lay.addLayout(bar)
        self.services_table = QTableWidget(0, 4)
        self.services_table.setHorizontalHeaderLabels([t("نام خدمت"), t("قیمت"), t("وضعیت"), t("عملیات")])
        self._setup_table(self.services_table)
        lay.addWidget(self.services_table)
        return tab

    def _add_service(self):
        dlg = _PriceDialog(self, "خدمت جدید")
        if dlg.exec():
            if service_model.exists(dlg.name.text()):
                QMessageBox.warning(self, t("خطا"), t("این خدمت قبلاً ثبت شده است."))
                return
            service_model.create(dlg.name.text(), dlg.price.value())
            self.refresh()

    def _edit_service(self, s):
        dlg = _PriceDialog(self, "ویرایش خدمت", s["name"], s["price"])
        if dlg.exec():
            service_model.update(s["id"], dlg.name.text(), dlg.price.value())
            self.refresh()

    def _delete_service(self, s):
        if QMessageBox.question(
            self, t("حذف"), t(f"خدمت «{s['name']}» حذف شود؟")
        ) == QMessageBox.StandardButton.Yes:
            service_model.delete(s["id"])
            self.refresh()

    # -- Treatments -------------------------------------------------------
    def _build_treatments_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        bar = QHBoxLayout()
        add_btn = QPushButton(t("➕ نوع معالجه جدید"))
        add_btn.clicked.connect(self._add_treatment)
        bar.addWidget(add_btn)
        bar.addStretch(1)
        lay.addLayout(bar)
        self.treatments_table = QTableWidget(0, 4)
        self.treatments_table.setHorizontalHeaderLabels([t("نوع معالجه"), t("قیمت پیش‌فرض"), t("وضعیت"), t("عملیات")])
        self._setup_table(self.treatments_table)
        lay.addWidget(self.treatments_table)
        return tab

    def _add_treatment(self):
        dlg = _PriceDialog(self, "نوع معالجه جدید")
        if dlg.exec():
            if treatment_model.exists(dlg.name.text()):
                QMessageBox.warning(self, t("خطا"), t("این معالجه قبلاً ثبت شده است."))
                return
            treatment_model.create(dlg.name.text(), dlg.price.value())
            self.refresh()

    def _edit_treatment(self, t):
        dlg = _PriceDialog(self, "ویرایش معالجه", t["name"], t["default_price"])
        if dlg.exec():
            treatment_model.update(t["id"], dlg.name.text(), dlg.price.value())
            self.refresh()

    def _delete_treatment(self, t):
        if QMessageBox.question(
            self, t("حذف"), t(f"معالجه «{t['name']}» حذف شود؟")
        ) == QMessageBox.StandardButton.Yes:
            treatment_model.delete(t["id"])
            self.refresh()

    # -- Helpers ----------------------------------------------------------
    def _setup_table(self, table):
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        prepare_table(table)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents)

    def _row_actions(self, edit_cb, del_cb):
        return actions_cell([
            make_button("ویرایش", "default", "ویرایش", lambda: edit_cb(None)),
            make_button("حذف", "danger", "حذف", lambda: del_cb(None)),
        ])

    def refresh(self):
        self.services_table.setRowCount(0)
        for s in service_model.all_services():
            r = self.services_table.rowCount()
            self.services_table.insertRow(r)
            self.services_table.setItem(r, 0, QTableWidgetItem(s["name"]))
            self.services_table.setItem(r, 1, QTableWidgetItem(
                helpers.format_money(s["price"])))
            self.services_table.setItem(r, 2, QTableWidgetItem(
                t("فعال") if s["is_active"] else t("غیرفعال")))
            self.services_table.setCellWidget(r, 3, self._row_actions(
                lambda _, ss=s: self._edit_service(ss),
                lambda _, ss=s: self._delete_service(ss)))

        self.treatments_table.setRowCount(0)
        for tr in treatment_model.all_treatments():
            r = self.treatments_table.rowCount()
            self.treatments_table.insertRow(r)
            self.treatments_table.setItem(r, 0, QTableWidgetItem(tr["name"]))
            self.treatments_table.setItem(r, 1, QTableWidgetItem(
                helpers.format_money(tr["default_price"])))
            self.treatments_table.setItem(r, 2, QTableWidgetItem(
                t("فعال") if tr["is_active"] else t("غیرفعال")))
            self.treatments_table.setCellWidget(r, 3, self._row_actions(
                lambda _, tt=tr: self._edit_treatment(tt),
                lambda _, tt=tr: self._delete_treatment(tt)))
