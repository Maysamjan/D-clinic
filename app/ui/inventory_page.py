"""Inventory / store-room management page.

Register medicines, equipment and consumables, track stock-in / stock-out
movements, and get low-stock and expiry alerts.
"""

from __future__ import annotations

import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget
)

from ..models import inventory as inv_model
from ..services import session
from ..utils import helpers
from .widgets.jalali_date_edit import JalaliDateEdit

UNITS = ["عدد", "بسته", "قطی", "بوتل", "میلی‌لیتر", "گرام", "کیلوگرام", "متر"]


# ---------------------------------------------------------------------------
# Item add / edit dialog
# ---------------------------------------------------------------------------

class ItemDialog(QDialog):
    def __init__(self, parent=None, item: dict | None = None):
        super().__init__(parent)
        self.item = item
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle("ویرایش قلم" if item else "ثبت قلم جدید (دوا / تجهیزات)")
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.name = QLineEdit()
        self.category = QComboBox()
        for key, label in inv_model.CATEGORIES.items():
            self.category.addItem(label, key)
        self.unit = QComboBox()
        self.unit.setEditable(True)
        self.unit.addItems(UNITS)
        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(0, 10_000_000)
        self.quantity.setDecimals(2)
        self.min_quantity = QDoubleSpinBox()
        self.min_quantity.setRange(0, 10_000_000)
        self.min_quantity.setDecimals(2)
        self.unit_price = QDoubleSpinBox()
        self.unit_price.setRange(0, 100_000_000)
        self.unit_price.setGroupSeparatorShown(True)
        self.unit_price.setSuffix(" افغانی")
        self.supplier = QLineEdit()

        self.has_expiry = QCheckBox("این قلم تاریخ انقضا دارد")
        self.expiry = JalaliDateEdit()
        self.expiry.setEnabled(False)
        self.has_expiry.toggled.connect(self.expiry.setEnabled)

        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(56)

        form.addRow("نام قلم *", self.name)
        form.addRow("دسته", self.category)
        form.addRow("واحد", self.unit)
        if not item:
            form.addRow("موجودی اولیه", self.quantity)
        form.addRow("حداقل موجودی (هشدار)", self.min_quantity)
        form.addRow("قیمت فی واحد", self.unit_price)
        form.addRow("تهیه‌کننده", self.supplier)
        form.addRow("", self.has_expiry)
        form.addRow("تاریخ انقضا", self.expiry)
        form.addRow("یادداشت", self.notes)
        layout.addLayout(form)

        if item:
            self.name.setText(item.get("name", ""))
            i = self.category.findData(item.get("category"))
            if i >= 0:
                self.category.setCurrentIndex(i)
            self.unit.setCurrentText(item.get("unit", ""))
            self.min_quantity.setValue(float(item.get("min_quantity") or 0))
            self.unit_price.setValue(float(item.get("unit_price") or 0))
            self.supplier.setText(item.get("supplier", ""))
            if item.get("expiry_date"):
                self.has_expiry.setChecked(True)
                self.expiry.set_iso(item["expiry_date"])
            self.notes.setPlainText(item.get("notes", ""))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "خطا", "نام قلم الزامی است.")
            return
        expiry = self.expiry.iso_date() if self.has_expiry.isChecked() else None
        if self.item:
            inv_model.update(
                self.item["id"], self.name.text(), self.category.currentData(),
                self.unit.currentText(), self.min_quantity.value(),
                self.unit_price.value(), self.supplier.text(), expiry,
                self.notes.toPlainText(), self.item.get("is_active", 1))
        else:
            inv_model.create(
                self.name.text(), self.category.currentData(),
                self.unit.currentText(), self.quantity.value(),
                self.min_quantity.value(), self.unit_price.value(),
                self.supplier.text(), expiry, self.notes.toPlainText())
        self.accept()


# ---------------------------------------------------------------------------
# Stock movement dialog
# ---------------------------------------------------------------------------

class StockDialog(QDialog):
    def __init__(self, parent=None, item: dict | None = None, mode: str = "in"):
        super().__init__(parent)
        self.item = item
        self.mode = mode  # in | out
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        title = "ورود به گدام" if mode == "in" else "خروج از گدام"
        self.setWindowTitle(title)
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)

        info = QLabel(f"{item.get('name','')} — موجودی فعلی: "
                      f"{helpers.jalali_digits(item.get('quantity',0))} "
                      f"{item.get('unit','')}")
        info.setStyleSheet("font-weight:700; color:#0B7D72;")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 10_000_000)
        self.amount.setDecimals(2)
        self.reason = QComboBox()
        if mode == "in":
            self.reason.addItem(inv_model.REASONS["purchase"], "purchase")
            self.reason.addItem(inv_model.REASONS["adjust"], "adjust")
        else:
            self.reason.addItem(inv_model.REASONS["use"], "use")
            self.reason.addItem(inv_model.REASONS["expire"], "expire")
            self.reason.addItem(inv_model.REASONS["adjust"], "adjust")
        self.date = JalaliDateEdit()
        self.note = QLineEdit()
        form.addRow("مقدار *", self.amount)
        form.addRow("علت", self.reason)
        form.addRow("تاریخ", self.date)
        form.addRow("یادداشت", self.note)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ثبت")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        if self.amount.value() <= 0:
            QMessageBox.warning(self, "خطا", "مقدار باید بیشتر از صفر باشد.")
            return
        change = self.amount.value() if self.mode == "in" else -self.amount.value()
        if self.mode == "out" and self.amount.value() > float(self.item.get("quantity", 0)):
            if QMessageBox.question(
                self, "هشدار",
                "مقدار خروج بیشتر از موجودی فعلی است. ادامه می‌دهید؟"
            ) != QMessageBox.StandardButton.Yes:
                return
        uid = session.current_user["id"] if session.current_user else None
        inv_model.adjust_stock(
            self.item["id"], change, self.reason.currentData(),
            self.note.text(), self.date.iso_date(), created_by=uid)
        self.accept()


# ---------------------------------------------------------------------------
# Inventory page
# ---------------------------------------------------------------------------

class InventoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        # Alerts banner
        self.alert = QLabel()
        self.alert.setWordWrap(True)
        self.alert.setVisible(False)
        layout.addWidget(self.alert)

        # Toolbar
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  جستجوی نام دوا، تجهیزات یا تهیه‌کننده ...")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("همه دسته‌ها", None)
        for key, label in inv_model.CATEGORIES.items():
            self.cat_filter.addItem(label, key)
        self.cat_filter.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.cat_filter)
        self.add_btn = QPushButton("➕ قلم جدید")
        self.add_btn.setMinimumHeight(42)
        self.add_btn.clicked.connect(self._add_item)
        bar.addWidget(self.add_btn)
        layout.addLayout(bar)

        self.count_label = QLabel()
        self.count_label.setObjectName("SectionHint")
        layout.addWidget(self.count_label)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "نام", "دسته", "موجودی", "واحد", "حداقل", "قیمت فی واحد",
            "ارزش کل", "تاریخ انقضا", "عملیات"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    # -- actions ----------------------------------------------------------
    def _add_item(self):
        dlg = ItemDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit_item(self, item):
        dlg = ItemDialog(self, item=item)
        if dlg.exec():
            self.refresh()

    def _stock(self, item, mode):
        dlg = StockDialog(self, item=item, mode=mode)
        if dlg.exec():
            self.refresh()

    def _delete_item(self, item):
        if QMessageBox.question(
            self, "حذف", f"قلم «{item['name']}» و سوابق آن حذف شود؟"
        ) == QMessageBox.StandardButton.Yes:
            inv_model.delete(item["id"])
            self.refresh()

    # -- refresh ----------------------------------------------------------
    def refresh(self):
        self._refresh_alerts()
        items = inv_model.all_items(
            category=self.cat_filter.currentData(),
            search=self.search.text())
        self.count_label.setText(
            f"{helpers.jalali_digits(len(items))} قلم  •  "
            f"ارزش کل گدام: {helpers.format_money(inv_model.total_value())}")
        today = datetime.date.today().isoformat()
        self.table.setRowCount(0)
        for it in items:
            r = self.table.rowCount()
            self.table.insertRow(r)
            name_item = QTableWidgetItem(it.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, it["id"])
            self.table.setItem(r, 0, name_item)
            self.table.setItem(r, 1, QTableWidgetItem(
                inv_model.CATEGORIES.get(it.get("category"), "")))
            qty_item = QTableWidgetItem(helpers.jalali_digits(
                _num(it.get("quantity"))))
            low = (it.get("min_quantity") or 0) > 0 and \
                float(it.get("quantity") or 0) <= float(it.get("min_quantity"))
            if low:
                qty_item.setForeground(QColor("#E11D48"))
                qty_item.setText(qty_item.text() + "  ⚠")
            self.table.setItem(r, 2, qty_item)
            self.table.setItem(r, 3, QTableWidgetItem(it.get("unit", "")))
            self.table.setItem(r, 4, QTableWidgetItem(
                helpers.jalali_digits(_num(it.get("min_quantity")))))
            self.table.setItem(r, 5, QTableWidgetItem(
                helpers.format_money(it.get("unit_price", 0))))
            self.table.setItem(r, 6, QTableWidgetItem(helpers.format_money(
                float(it.get("quantity") or 0) * float(it.get("unit_price") or 0))))
            exp = it.get("expiry_date")
            exp_item = QTableWidgetItem(helpers.jalali_date(exp) if exp else "—")
            if exp and exp <= today:
                exp_item.setForeground(QColor("#E11D48"))
            self.table.setItem(r, 7, exp_item)
            self.table.setCellWidget(r, 8, self._actions(it))

    def _actions(self, it):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)
        in_btn = QPushButton("＋")
        in_btn.setObjectName("Success")
        in_btn.setFixedWidth(38)
        in_btn.setToolTip("ورود به گدام")
        in_btn.clicked.connect(lambda _, x=it: self._stock(x, "in"))
        out_btn = QPushButton("－")
        out_btn.setObjectName("Ghost")
        out_btn.setFixedWidth(38)
        out_btn.setToolTip("خروج از گدام")
        out_btn.clicked.connect(lambda _, x=it: self._stock(x, "out"))
        edit_btn = QPushButton("✎")
        edit_btn.setObjectName("IconBtn")
        edit_btn.setFixedWidth(38)
        edit_btn.setToolTip("ویرایش")
        edit_btn.clicked.connect(lambda _, x=it: self._edit_item(x))
        del_btn = QPushButton("🗑")
        del_btn.setObjectName("Danger")
        del_btn.setFixedWidth(38)
        del_btn.setToolTip("حذف")
        del_btn.clicked.connect(lambda _, x=it: self._delete_item(x))
        for b in (in_btn, out_btn, edit_btn, del_btn):
            lay.addWidget(b)
        return w

    def _refresh_alerts(self):
        low = inv_model.low_stock()
        expiring = inv_model.expiring_soon(60)
        parts = []
        if low:
            parts.append(f"⚠ {helpers.jalali_digits(len(low))} قلم به حداقل موجودی رسیده‌اند")
        if expiring:
            parts.append(f"⏰ {helpers.jalali_digits(len(expiring))} قلم نزدیک به تاریخ انقضا هستند")
        if parts:
            self.alert.setText("   •   ".join(parts))
            self.alert.setStyleSheet(
                "background:#FEF2F4; color:#B11334; border:1px solid #F6C9D2;"
                "border-radius:10px; padding:10px 14px; font-weight:700;")
            self.alert.setVisible(True)
        else:
            self.alert.setVisible(False)


def _num(value) -> str:
    """Format a stock number without trailing .0 for whole numbers."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    return str(int(v)) if v == int(v) else f"{v:.2f}"
