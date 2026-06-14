"""Clinic settings, logo and backup/restore page."""

from __future__ import annotations

import os
import shutil
import time

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget
)

from .. import config
from ..models import clinic as clinic_model
from ..models import user as user_model
from ..services import backup_service, session
from ..utils import helpers
from PyQt6.QtWidgets import QComboBox
from ..services import i18n
from ..services.i18n import t


class SettingsPage(QWidget):
    clinic_updated = pyqtSignal()
    data_restored = pyqtSignal()
    language_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logo_path = ""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(16)
        top.addWidget(self._build_clinic_card(), 1)

        right = QVBoxLayout()
        right.setSpacing(16)
        right.addWidget(self._build_backup_card(), 1)
        right.addWidget(self._build_password_card())
        top.addLayout(right, 1)
        root.addLayout(top)
        root.addStretch(1)

    def _build_clinic_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        title = QLabel(t("تنظیمات کلینیک"))
        title.setObjectName("CardTitle")
        lay.addWidget(title)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(t("زبان برنامه") + ":"))
        self.language = QComboBox()
        self.language.addItem("فارسی / دری", "fa")
        self.language.addItem("English", "en")
        _li = self.language.findData(i18n.get_language())
        if _li >= 0:
            self.language.setCurrentIndex(_li)
        lang_row.addWidget(self.language, 1)
        lay.addLayout(lang_row)

        # Logo
        logo_row = QHBoxLayout()
        self.logo_preview = QLabel(t("بدون لوگو"))
        self.logo_preview.setFixedSize(96, 96)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet(
            "border:1px dashed #cfd8e3; border-radius:12px; color:#94a3b8;")
        logo_btns = QVBoxLayout()
        pick_btn = QPushButton(t("انتخاب لوگو"))
        pick_btn.setObjectName("Secondary")
        pick_btn.clicked.connect(self._pick_logo)
        clear_btn = QPushButton(t("حذف لوگو"))
        clear_btn.setObjectName("Secondary")
        clear_btn.clicked.connect(self._clear_logo)
        logo_btns.addWidget(pick_btn)
        logo_btns.addWidget(clear_btn)
        logo_btns.addStretch(1)
        logo_row.addWidget(self.logo_preview)
        logo_row.addLayout(logo_btns)
        logo_row.addStretch(1)
        lay.addLayout(logo_row)

        form = QFormLayout()
        form.setSpacing(10)
        self.name = QLineEdit()
        self.owner = QLineEdit()
        self.phone = QLineEdit()
        self.city = QLineEdit()
        self.address = QLineEdit()
        self.email = QLineEdit()
        form.addRow(t("نام کلینیک *"), self.name)
        form.addRow(t("نام داکتر / مالک"), self.owner)
        form.addRow(t("شماره تلفن"), self.phone)
        form.addRow(t("شهر"), self.city)
        form.addRow(t("آدرس"), self.address)
        form.addRow(t("ایمیل (اختیاری)"), self.email)
        lay.addLayout(form)

        save_btn = QPushButton(t("ذخیره تنظیمات"))
        save_btn.clicked.connect(self._save_clinic)
        lay.addWidget(save_btn)
        lay.addStretch(1)
        return card

    def _build_backup_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        title = QLabel(t("پشتیبان‌گیری و بازیابی"))
        title.setObjectName("CardTitle")
        lay.addWidget(title)

        desc = QLabel(t("نسخه پشتیبان به‌صورت خودکار هر روز گرفته می‌شود. "
            "می‌توانید به‌صورت دستی نیز پشتیبان بگیرید یا اطلاعات را بازیابی کنید."))
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#64748b;")
        lay.addWidget(desc)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton(t("💾 پشتیبان‌گیری اکنون"))
        backup_btn.setObjectName("Success")
        backup_btn.clicked.connect(self._manual_backup)
        export_btn = QPushButton(t("📤 ذخیره در محل دلخواه"))
        export_btn.setObjectName("Secondary")
        export_btn.clicked.connect(self._export_backup)
        restore_btn = QPushButton(t("♻ بازیابی از فایل"))
        restore_btn.setObjectName("Danger")
        restore_btn.clicked.connect(self._restore_backup)
        btn_row.addWidget(backup_btn)
        btn_row.addWidget(export_btn)
        btn_row.addWidget(restore_btn)
        lay.addLayout(btn_row)

        lay.addWidget(QLabel(t("تاریخچه پشتیبان‌ها:")))
        self.backups_table = QTableWidget(0, 4)
        self.backups_table.setHorizontalHeaderLabels([t("تاریخ"), t("نوع"), t("حجم"), t("وضعیت")])
        self.backups_table.verticalHeader().setVisible(False)
        self.backups_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.backups_table, 1)
        return card

    def _build_password_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)

        title = QLabel(t("تغییر رمز عبور"))
        title.setObjectName("CardTitle")
        lay.addWidget(title)
        who = session.current_user or {}
        sub = QLabel(t("کاربر: ") + (who.get("full_name") or who.get("username", "")))
        sub.setObjectName("SectionHint")
        lay.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.cur_pw = QLineEdit()
        self.cur_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pw = QLineEdit()
        self.new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pw2 = QLineEdit()
        self.new_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(t("رمز عبور فعلی"), self.cur_pw)
        form.addRow(t("رمز عبور جدید"), self.new_pw)
        form.addRow(t("تکرار رمز جدید"), self.new_pw2)
        lay.addLayout(form)

        btn = QPushButton(t("تغییر رمز عبور"))
        btn.clicked.connect(self._change_password)
        lay.addWidget(btn)
        lay.addStretch(1)
        return card

    def _change_password(self):
        if not session.current_user:
            return
        cur = self.cur_pw.text()
        new = self.new_pw.text()
        new2 = self.new_pw2.text()
        if not cur or not new:
            QMessageBox.warning(self, t("خطا"), t("همه فیلدها را پر کنید."))
            return
        if len(new) < 4:
            QMessageBox.warning(self, t("خطا"), t("رمز جدید باید حداقل ۴ حرف باشد."))
            return
        if new != new2:
            QMessageBox.warning(self, t("خطا"), t("رمز جدید و تکرار آن یکسان نیستند."))
            return
        if user_model.change_password(session.current_user["id"], cur, new):
            QMessageBox.information(self, t("موفق"), t("رمز عبور با موفقیت تغییر کرد."))
            self.cur_pw.clear()
            self.new_pw.clear()
            self.new_pw2.clear()
        else:
            QMessageBox.critical(self, t("خطا"), t("رمز عبور فعلی اشتباه است."))

    # -- Logo -------------------------------------------------------------
    def _pick_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب لوگو", "", "تصاویر (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        config.ensure_dirs()
        ext = os.path.splitext(path)[1]
        dest = os.path.join(config.LOGO_DIR, f"logo_{int(time.time())}{ext}")
        shutil.copy2(path, dest)
        self._logo_path = dest
        self._show_logo(dest)

    def _clear_logo(self):
        self._logo_path = ""
        self.logo_preview.setPixmap(QPixmap())
        self.logo_preview.setText(t("بدون لوگو"))

    def _show_logo(self, path):
        if path and os.path.isfile(path):
            pix = QPixmap(path).scaled(
                92, 92, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            self.logo_preview.setPixmap(pix)
            self.logo_preview.setText("")
        else:
            self.logo_preview.setText(t("بدون لوگو"))

    # -- Clinic save ------------------------------------------------------
    def _save_clinic(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, t("خطا"), t("نام کلینیک الزامی است."))
            return
        clinic_model.update(
            self.name.text().strip(), self.owner.text().strip(),
            self.phone.text().strip(), self.address.text().strip(),
            self.email.text().strip(), self._logo_path,
            city=self.city.text().strip(),
        )
        new_lang = self.language.currentData()
        lang_changed = new_lang != i18n.get_language()
        if lang_changed:
            clinic_model.set_language(new_lang)
        QMessageBox.information(self, t("ذخیره شد"), t("تنظیمات کلینیک ذخیره شد."))
        self.clinic_updated.emit()
        if lang_changed:
            self.language_changed.emit()

    # -- Backups ----------------------------------------------------------
    def _manual_backup(self):
        try:
            path = backup_service.create_backup("manual")
            QMessageBox.information(self, t("موفق"), t("پشتیبان ساخته شد:\n") + path)
            self._load_backups()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("خطا"), t("پشتیبان‌گیری ناموفق بود:\n") + str(exc))

    def _export_backup(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "ذخیره پشتیبان",
            os.path.join(config.BASE_DIR,
                         f"dclinic_backup_{time.strftime('%Y%m%d')}.db"),
            "پایگاه داده (*.db)")
        if not dest:
            return
        try:
            backup_service.create_backup("manual", dest_path=dest)
            QMessageBox.information(self, t("موفق"), t("پشتیبان ذخیره شد:\n") + dest)
            self._load_backups()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "خطا", str(exc))

    def _restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب فایل پشتیبان", config.BACKUP_DIR,
            "پایگاه داده (*.db)")
        if not path:
            return
        confirm = QMessageBox.warning(
            self, t("بازیابی اطلاعات"),
            t("تمام اطلاعات فعلی با اطلاعات فایل پشتیبان جایگزین می‌شود.\n"
              "یک نسخه ایمنی از وضعیت فعلی به‌صورت خودکار ساخته خواهد شد.\n\n"
              "ادامه می‌دهید؟"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            backup_service.restore_backup(path)
            QMessageBox.information(self, t("موفق"), t("اطلاعات با موفقیت بازیابی شد."))
            self.data_restored.emit()
            self.refresh()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, t("خطا"), t("بازیابی ناموفق بود:\n") + str(exc))

    def _load_backups(self):
        self.backups_table.setRowCount(0)
        for b in backup_service.list_backups():
            r = self.backups_table.rowCount()
            self.backups_table.insertRow(r)
            self.backups_table.setItem(r, 0, QTableWidgetItem(
                helpers.jalali_date(b.get("created_at"))))
            kind = {"auto": t("خودکار"), "manual": t("دستی")}.get(
                b.get("kind"), b.get("kind", ""))
            self.backups_table.setItem(r, 1, QTableWidgetItem(kind))
            size_kb = (b.get("size_bytes") or 0) / 1024
            self.backups_table.setItem(r, 2, QTableWidgetItem(
                helpers.jalali_digits(f"{size_kb:,.0f}") + " KB"))
            status = "موجود" if b.get("exists") else "حذف شده"
            self.backups_table.setItem(r, 3, QTableWidgetItem(status))

    # -- Refresh ----------------------------------------------------------
    def refresh(self):
        c = clinic_model.get()
        self.name.setText(c.get("name", ""))
        self.owner.setText(c.get("owner_name", ""))
        self.phone.setText(c.get("phone", ""))
        self.city.setText(c.get("city", "") or "")
        self.address.setText(c.get("address", ""))
        self.email.setText(c.get("email", ""))
        self._logo_path = c.get("logo_path", "") or ""
        self._show_logo(self._logo_path)
        self._load_backups()
