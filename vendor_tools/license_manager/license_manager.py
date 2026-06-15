"""Zenith Soft License Manager — vendor-only desktop tool.

A simple PyQt6 desktop interface for the software owner to generate DEMO/FULL
D-Clinic product keys without using the command line, with a searchable history
of everything issued.

CONFIDENTIAL: for Zenith Soft only. Never ship this tool, its database, or the
private key to customers.
"""

from __future__ import annotations

import datetime
import os
import sys

# Allow running both as a script and when frozen (flat module layout).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget
)

import licensing_core as core
import history_db as db

APP_TITLE = "Zenith Soft License Manager"
APP_VERSION = "1.0.0"

_QSS = """
QWidget { font-family: "Segoe UI", "Vazirmatn", sans-serif; font-size: 14px;
          color: #14253B; background: #EEF3F8; }
QFrame#Card { background: #ffffff; border: 1px solid #E7EDF4; border-radius: 14px; }
QLabel#Title { font-size: 20px; font-weight: 700; color: #0B2A33; }
QLabel#Warn { background: #FEF2F4; color: #B11334; border: 1px solid #F6C9D2;
              border-radius: 8px; padding: 8px 12px; font-weight: 700; }
QLabel#Section { font-size: 15px; font-weight: 700; color: #0E9F8E; }
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {
    background: #ffffff; border: 1px solid #D4DEEA; border-radius: 8px;
    padding: 8px 10px; min-height: 20px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #0E9F8E; }
QPushButton { background: #0E9F8E; color: #fff; border: none; border-radius: 8px;
              padding: 10px 18px; font-weight: 700; }
QPushButton:hover { background: #0C8E7F; }
QPushButton#Secondary { background: #F1F5FA; color: #2A3B52; border: 1px solid #D4DEEA; }
QPushButton#Secondary:hover { background: #E6EDF5; }
QTableWidget { background: #fff; border: 1px solid #E7EDF4; border-radius: 10px;
               gridline-color: #EEF2F7; selection-background-color: #E3F6F3;
               selection-color: #0A6B61; }
QHeaderView::section { background: #F4F7FB; color: #51627A; padding: 9px;
               border: none; border-bottom: 2px solid #E3EAF2; font-weight: 700; }
QTabBar::tab { padding: 9px 18px; font-weight: 600; color: #65788F;
               border-bottom: 3px solid transparent; }
QTabBar::tab:selected { color: #0E9F8E; border-bottom: 3px solid #0E9F8E; }
QTabWidget::pane { border: 1px solid #E7EDF4; border-radius: 10px; background: #fff; }
"""


class GenerateTab(QWidget):
    def __init__(self, on_generated):
        super().__init__()
        self._on_generated = on_generated
        self._last_path = ""
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # -- left: form ---------------------------------------------------
        form_card = QFrame(); form_card.setObjectName("Card")
        fl = QVBoxLayout(form_card); fl.setContentsMargins(18, 18, 18, 18); fl.setSpacing(10)
        fl.addWidget(self._section("Customer & machine"))
        form = QFormLayout(); form.setSpacing(10)
        self.machine_id = QLineEdit(); self.machine_id.setPlaceholderText("e.g. CB103-6007C-2FA0C-6EF63")
        self.clinic_name = QLineEdit()
        self.phone = QLineEdit()
        self.city = QLineEdit()
        form.addRow("Machine ID *", self.machine_id)
        form.addRow("Clinic Name", self.clinic_name)
        form.addRow("Customer Phone", self.phone)
        form.addRow("City", self.city)
        fl.addLayout(form)

        fl.addWidget(self._section("License"))
        lic_form = QFormLayout(); lic_form.setSpacing(10)
        self.ltype = QComboBox(); self.ltype.addItems([core.TYPE_DEMO, core.TYPE_FULL])
        self.ltype.currentTextChanged.connect(self._toggle_demo)
        lic_form.addRow("License Type", self.ltype)

        self.days = QComboBox(); self.days.addItems(["7", "14", "30", "Custom"])
        self.days.setCurrentText("14")
        self.days.currentTextChanged.connect(self._toggle_custom)
        self.days_custom = QSpinBox(); self.days_custom.setRange(1, 3650)
        self.days_custom.setValue(14); self.days_custom.setSuffix(" days"); self.days_custom.hide()
        days_row = QHBoxLayout(); days_row.addWidget(self.days, 1); days_row.addWidget(self.days_custom, 1)
        lic_form.addRow("DEMO days", days_row)

        self.maxpat = QComboBox(); self.maxpat.addItems(["50", "100", "Unlimited", "Custom"])
        self.maxpat.currentTextChanged.connect(self._toggle_custom)
        self.maxpat_custom = QSpinBox(); self.maxpat_custom.setRange(1, 1000000)
        self.maxpat_custom.setValue(50); self.maxpat_custom.hide()
        max_row = QHBoxLayout(); max_row.addWidget(self.maxpat, 1); max_row.addWidget(self.maxpat_custom, 1)
        lic_form.addRow("Max patients", max_row)
        fl.addLayout(lic_form)

        gen_btn = QPushButton("⚙  Generate License")
        gen_btn.setMinimumHeight(44)
        gen_btn.clicked.connect(self._generate)
        fl.addWidget(gen_btn)
        fl.addStretch(1)
        root.addWidget(form_card, 1)

        # -- right: output ------------------------------------------------
        out_card = QFrame(); out_card.setObjectName("Card")
        ol = QVBoxLayout(out_card); ol.setContentsMargins(18, 18, 18, 18); ol.setSpacing(10)
        ol.addWidget(self._section("Product Key"))
        self.output = QPlainTextEdit(); self.output.setReadOnly(True)
        self.output.setPlaceholderText("The generated Product Key (DCL2...) will appear here.")
        self.output.setMinimumHeight(160)
        ol.addWidget(self.output)
        self.meta = QLabel(""); self.meta.setWordWrap(True); self.meta.setStyleSheet("color:#46515F;")
        ol.addWidget(self.meta)
        btns = QHBoxLayout()
        self.copy_btn = QPushButton("📋  Copy Product Key"); self.copy_btn.setObjectName("Secondary")
        self.copy_btn.clicked.connect(self._copy); self.copy_btn.setEnabled(False)
        self.open_btn = QPushButton("📁  Open .lic folder"); self.open_btn.setObjectName("Secondary")
        self.open_btn.clicked.connect(self._open_folder); self.open_btn.setEnabled(False)
        btns.addWidget(self.copy_btn); btns.addWidget(self.open_btn)
        ol.addLayout(btns)
        ol.addStretch(1)
        root.addWidget(out_card, 1)

        self._toggle_demo(self.ltype.currentText())
        self._toggle_custom()

    def _section(self, text):
        lbl = QLabel(text); lbl.setObjectName("Section"); return lbl

    def _toggle_demo(self, ltype):
        is_demo = ltype == core.TYPE_DEMO
        for w in (self.days, self.days_custom, self.maxpat, self.maxpat_custom):
            w.setEnabled(is_demo)
        self._toggle_custom()

    def _toggle_custom(self, *_):
        self.days_custom.setVisible(self.days.currentText() == "Custom")
        self.maxpat_custom.setVisible(self.maxpat.currentText() == "Custom")

    def _resolved_days(self):
        return self.days_custom.value() if self.days.currentText() == "Custom" \
            else int(self.days.currentText())

    def _resolved_max(self):
        choice = self.maxpat.currentText()
        if choice == "Unlimited":
            return 0
        if choice == "Custom":
            return self.maxpat_custom.value()
        return int(choice)

    def _generate(self):
        mid = self.machine_id.text().strip()
        if not core.is_valid_machine_id(mid):
            QMessageBox.warning(self, "Invalid Machine ID",
                "The Machine ID must be 20 hex characters,\n"
                "e.g. CB103-6007C-2FA0C-6EF63.")
            return
        ltype = self.ltype.currentText()
        days = self._resolved_days() if ltype == core.TYPE_DEMO else None
        cap = self._resolved_max() if ltype == core.TYPE_DEMO else 0
        try:
            result = core.generate_license(ltype, mid, days=days, max_patients=cap)
            path = core.write_license_file(result, self.clinic_name.text(), days)
        except core.LicensingError as exc:
            QMessageBox.critical(self, "Cannot generate", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Error", str(exc))
            return

        self._last_path = path
        self.output.setPlainText(result["product_key"])
        exp = result["expiry_date"].isoformat() if result["expiry_date"] else "—"
        cap_txt = "Unlimited" if not result["max_patients"] else str(result["max_patients"])
        self.meta.setText(
            f"Type: {result['license_type']}   ·   Expiry: {exp}   ·   "
            f"Max patients: {cap_txt}\nSaved: {path}")
        self.copy_btn.setEnabled(True)
        self.open_btn.setEnabled(True)

        db.add({
            "clinic_name": self.clinic_name.text().strip(),
            "customer_phone": self.phone.text().strip(),
            "city": self.city.text().strip(),
            "machine_id": result["machine_id"],
            "license_type": result["license_type"],
            "demo_days": days,
            "patient_limit": result["max_patients"],
            "generated_date": result["issue_date"].isoformat(),
            "expiry_date": exp if exp != "—" else None,
            "product_key": result["product_key"],
            "license_path": path,
        })
        QMessageBox.information(self, "License generated",
            f"{result['license_type']} license created and saved:\n{path}")
        if self._on_generated:
            self._on_generated()

    def _copy(self):
        QGuiApplication.clipboard().setText(self.output.toPlainText())
        QMessageBox.information(self, "Copied", "Product Key copied to clipboard.")

    def _open_folder(self):
        folder = os.path.dirname(self._last_path) or core.output_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class HistoryTab(QWidget):
    COLS = ["Date", "Clinic", "Phone", "City", "Machine ID", "Type",
            "Days", "Limit", "Expiry"]

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(16, 16, 16, 16); root.setSpacing(12)

        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by clinic name, phone or Machine ID ...")
        self.search.textChanged.connect(self.refresh)
        self.filter = QComboBox(); self.filter.addItems(["ALL", core.TYPE_DEMO, core.TYPE_FULL])
        self.filter.currentTextChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)
        bar.addWidget(QLabel("Type:"))
        bar.addWidget(self.filter)
        root.addLayout(bar)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._copy_selected)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        copy_btn = QPushButton("📋  Copy Product Key"); copy_btn.setObjectName("Secondary")
        copy_btn.clicked.connect(self._copy_selected)
        open_btn = QPushButton("📁  Open .lic location"); open_btn.setObjectName("Secondary")
        open_btn.clicked.connect(self._open_selected)
        actions.addStretch(1); actions.addWidget(copy_btn); actions.addWidget(open_btn)
        root.addLayout(actions)
        self.refresh()

    def refresh(self):
        rows = db.search(self.search.text(), self.filter.currentText())
        self.table.setRowCount(0)
        for rec in rows:
            r = self.table.rowCount(); self.table.insertRow(r)
            cells = [
                rec["generated_date"], rec["clinic_name"], rec["customer_phone"],
                rec["city"], core.machine_id_display(rec["machine_id"]),
                rec["license_type"],
                str(rec["demo_days"]) if rec["demo_days"] else "—",
                "∞" if not rec["patient_limit"] else str(rec["patient_limit"]),
                rec["expiry_date"] or "—",
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                if c == 0:  # stash the full record on the first cell
                    item.setData(Qt.ItemDataRole.UserRole, dict(rec))
                self.table.setItem(r, c, item)

    def _selected_record(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _copy_selected(self):
        rec = self._selected_record()
        if not rec:
            QMessageBox.information(self, "No selection", "Select a row first.")
            return
        QGuiApplication.clipboard().setText(rec["product_key"])
        QMessageBox.information(self, "Copied", "Product Key copied to clipboard.")

    def _open_selected(self):
        rec = self._selected_record()
        if not rec:
            QMessageBox.information(self, "No selection", "Select a row first.")
            return
        path = rec.get("license_path") or ""
        folder = os.path.dirname(path) if path else core.output_dir()
        if not os.path.isdir(folder):
            folder = core.output_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE}  v{APP_VERSION}")
        self.resize(1080, 720)
        root = QVBoxLayout(self); root.setContentsMargins(16, 14, 16, 16); root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(APP_TITLE); title.setObjectName("Title")
        header.addWidget(title); header.addStretch(1)
        kp = self._key_status_label()
        header.addWidget(kp)
        root.addLayout(header)

        warn = QLabel("⚠  CONFIDENTIAL — This tool is for Zenith Soft only. "
                      "Never share it, its database, or the private key with customers.")
        warn.setObjectName("Warn"); warn.setWordWrap(True)
        root.addWidget(warn)

        tabs = QTabWidget()
        self.history = HistoryTab()
        self.generate = GenerateTab(on_generated=self.history.refresh)
        tabs.addTab(self.generate, "Generate License")
        tabs.addTab(self.history, "License History")
        root.addWidget(tabs, 1)

    def _key_status_label(self) -> QLabel:
        path = core.private_key_path()
        if path:
            lbl = QLabel("🔐  Private key loaded")
            lbl.setStyleSheet("color:#0A8F60; font-weight:700;")
        else:
            lbl = QLabel("⛔  Private key NOT found")
            lbl.setStyleSheet("color:#C0344E; font-weight:700;")
        return lbl


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyleSheet(_QSS)
    # If the private key is missing, warn up-front (but still allow browsing history).
    if core.private_key_path() is None:
        QMessageBox.warning(
            None, APP_TITLE,
            "Private key not found.\n\n"
            "Place your vendor key at:\n    license_private/private_key.hex\n"
            "next to this tool (or in the D-Clinic project root).\n\n"
            "You can still view history, but cannot generate new keys until the "
            "private key is present.")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
