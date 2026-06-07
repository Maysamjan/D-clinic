"""Invoice creation dialog with line items."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout
)

from ..models import invoice as invoice_model
from ..models import service_price as service_model
from ..services import session
from ..utils import helpers


class InvoiceDialog(QDialog):
    def __init__(self, parent=None, patient_id: int = 0):
        super().__init__(parent)
        self.patient_id = patient_id
        self.invoice_id = None
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("صدور صورتحساب")
        self.setMinimumWidth(520)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        # Add-item row
        add_row = QHBoxLayout()
        self.service = QComboBox()
        self.service.addItem("— خدمت سفارشی —", None)
        for s in service_model.all_active():
            self.service.addItem(s["name"], s["price"])
        self.service.currentIndexChanged.connect(self._on_service_changed)
        self.desc = QLineEdit()
        self.desc.setPlaceholderText("شرح خدمت")
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setSingleStep(100)
        self.amount.setGroupSeparatorShown(True)
        add_btn = QPushButton("افزودن")
        add_btn.setObjectName("Success")
        add_btn.clicked.connect(self._add_item)
        add_row.addWidget(self.service)
        add_row.addWidget(self.desc, 1)
        add_row.addWidget(self.amount)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        # Items table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["شرح", "مبلغ", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 60)
        self.table.horizontalHeader().setSectionResizeMode(
            0, self.table.horizontalHeader().ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Total + paid
        bottom = QHBoxLayout()
        self.total_label = QLabel("مجموع: ۰ افغانی")
        self.total_label.setStyleSheet(
            "font-size:16px; font-weight:bold; color:#2563eb;")
        bottom.addWidget(self.total_label)
        bottom.addStretch(1)
        bottom.addWidget(QLabel("پرداخت شده:"))
        self.paid = QDoubleSpinBox()
        self.paid.setRange(0, 100_000_000)
        self.paid.setSingleStep(100)
        self.paid.setGroupSeparatorShown(True)
        bottom.addWidget(self.paid)
        layout.addLayout(bottom)

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("یادداشت (اختیاری)")
        layout.addWidget(self.notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("صدور و چاپ")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_service_changed(self):
        price = self.service.currentData()
        if price is not None:
            self.desc.setText(self.service.currentText())
            self.amount.setValue(float(price))

    def _add_item(self):
        desc = self.desc.text().strip()
        amount = self.amount.value()
        if not desc:
            QMessageBox.warning(self, "خطا", "شرح خدمت را وارد کنید.")
            return
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setItem(r, 0, QTableWidgetItem(desc))
        amt_item = QTableWidgetItem(helpers.format_money(amount))
        amt_item.setData(Qt.ItemDataRole.UserRole, amount)
        self.table.setItem(r, 1, amt_item)
        rm = QPushButton("🗑")
        rm.setObjectName("Danger")
        rm.clicked.connect(lambda: self._remove_row(amt_item))
        self.table.setCellWidget(r, 2, rm)
        self.desc.clear()
        self.amount.setValue(0)
        self.service.setCurrentIndex(0)
        self._update_total()

    def _remove_row(self, amt_item):
        self.table.removeRow(amt_item.row())
        self._update_total()

    def _items(self):
        items = []
        for r in range(self.table.rowCount()):
            desc = self.table.item(r, 0).text()
            amount = self.table.item(r, 1).data(Qt.ItemDataRole.UserRole)
            items.append((desc, float(amount)))
        return items

    def _update_total(self):
        total = sum(a for _, a in self._items())
        self.total_label.setText("مجموع: " + helpers.format_money(total))
        if self.paid.value() == 0:
            self.paid.setValue(total)

    def _save(self):
        items = self._items()
        if not items:
            QMessageBox.warning(self, "خطا", "حداقل یک ردیف خدمت اضافه کنید.")
            return
        uid = session.current_user["id"] if session.current_user else None
        self.invoice_id = invoice_model.create(
            self.patient_id, items, paid=self.paid.value(),
            notes=self.notes.text(), created_by=uid,
        )
        self.accept()
