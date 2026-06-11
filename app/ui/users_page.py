"""User management page (admin only)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from .. import config
from ..models import user as user_model
from ..services import session
from ..services.i18n import t
from .widgets.actions import actions_cell, make_button, prepare_table


class UserDialog(QDialog):
    def __init__(self, parent=None, user: dict | None = None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("ویرایش کاربر" if user else "کاربر جدید")
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.username = QLineEdit()
        self.full_name = QLineEdit()
        self.role = QComboBox()
        for key in (config.ROLE_ADMIN, config.ROLE_DOCTOR, config.ROLE_RECEPTIONIST):
            self.role.addItem(config.ROLE_LABELS[key], key)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.status = QComboBox()
        self.status.addItem(t("فعال"), 1)
        self.status.addItem(t("غیرفعال"), 0)

        form.addRow(t("نام کاربری *"), self.username)
        form.addRow(t("نام مکمل"), self.full_name)
        form.addRow(t("نقش"), self.role)
        pw_label = "رمز عبور (خالی = بدون تغییر)" if user else "رمز عبور *"
        form.addRow(pw_label, self.password)
        form.addRow(t("وضعیت"), self.status)
        layout.addLayout(form)

        if user:
            self.username.setText(user.get("username", ""))
            self.username.setReadOnly(True)
            self.full_name.setText(user.get("full_name", ""))
            i = self.role.findData(user.get("role"))
            if i >= 0:
                self.role.setCurrentIndex(i)
            self.status.setCurrentIndex(0 if user.get("is_active", 1) else 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("ذخیره")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("لغو")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        username = self.username.text().strip()
        if not username:
            QMessageBox.warning(self, t("خطا"), t("نام کاربری الزامی است."))
            return
        pw = self.password.text()
        if self.user:
            user_model.update(
                self.user["id"], self.full_name.text(),
                self.role.currentData(), self.status.currentData(),
                password=pw or None)
        else:
            if not pw:
                QMessageBox.warning(self, t("خطا"), t("رمز عبور الزامی است."))
                return
            if user_model.username_exists(username):
                QMessageBox.warning(self, t("خطا"), t("این نام کاربری قبلاً ثبت شده است."))
                return
            user_model.create(username, pw, self.full_name.text(),
                              self.role.currentData())
        self.accept()


class UsersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        bar = QHBoxLayout()
        add_btn = QPushButton(t("➕ کاربر جدید"))
        add_btn.clicked.connect(self._add_user)
        bar.addWidget(add_btn)
        bar.addStretch(1)
        layout.addLayout(bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("نام کاربری"), t("نام مکمل"), t("نقش"), t("وضعیت"), t("عملیات")])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        prepare_table(self.table)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def _add_user(self):
        dlg = UserDialog(self)
        if dlg.exec():
            self.refresh()

    def _edit_user(self, u):
        dlg = UserDialog(self, user=u)
        if dlg.exec():
            self.refresh()

    def _delete_user(self, u):
        if session.current_user and u["id"] == session.current_user["id"]:
            QMessageBox.warning(self, t("خطا"), t("نمی‌توانید کاربر فعال فعلی را حذف کنید."))
            return
        if user_model.count() <= 1:
            QMessageBox.warning(self, t("خطا"), t("حداقل یک کاربر باید باقی بماند."))
            return
        if QMessageBox.question(
            self, t("حذف کاربر"), t(f"کاربر «{u.get('username')}» حذف شود؟")
        ) == QMessageBox.StandardButton.Yes:
            user_model.delete(u["id"])
            self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        for u in user_model.all_users():
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(u.get("username", "")))
            self.table.setItem(r, 1, QTableWidgetItem(u.get("full_name", "")))
            self.table.setItem(r, 2, QTableWidgetItem(
                config.ROLE_LABELS.get(u.get("role"), u.get("role", ""))))
            self.table.setItem(r, 3, QTableWidgetItem(
                t("فعال") if u.get("is_active") else t("غیرفعال")))
            self.table.setCellWidget(r, 4, actions_cell([
                make_button("ویرایش", "default", "ویرایش کاربر",
                            lambda uu=u: self._edit_user(uu)),
                make_button("حذف", "danger", "حذف کاربر",
                            lambda uu=u: self._delete_user(uu)),
            ]))
