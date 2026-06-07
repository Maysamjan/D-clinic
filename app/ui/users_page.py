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


class UserDialog(QDialog):
    def __init__(self, parent=None, user: dict | None = None):
        super().__init__(parent)
        self.user = user
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
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
        self.status.addItem("فعال", 1)
        self.status.addItem("غیرفعال", 0)

        form.addRow("نام کاربری *", self.username)
        form.addRow("نام مکمل", self.full_name)
        form.addRow("نقش", self.role)
        pw_label = "رمز عبور (خالی = بدون تغییر)" if user else "رمز عبور *"
        form.addRow(pw_label, self.password)
        form.addRow("وضعیت", self.status)
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
            QMessageBox.warning(self, "خطا", "نام کاربری الزامی است.")
            return
        pw = self.password.text()
        if self.user:
            user_model.update(
                self.user["id"], self.full_name.text(),
                self.role.currentData(), self.status.currentData(),
                password=pw or None)
        else:
            if not pw:
                QMessageBox.warning(self, "خطا", "رمز عبور الزامی است.")
                return
            if user_model.username_exists(username):
                QMessageBox.warning(self, "خطا", "این نام کاربری قبلاً ثبت شده است.")
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
        add_btn = QPushButton("➕ کاربر جدید")
        add_btn.clicked.connect(self._add_user)
        bar.addWidget(add_btn)
        bar.addStretch(1)
        layout.addLayout(bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "نام کاربری", "نام مکمل", "نقش", "وضعیت", "عملیات"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
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
            QMessageBox.warning(self, "خطا", "نمی‌توانید کاربر فعال فعلی را حذف کنید.")
            return
        if user_model.count() <= 1:
            QMessageBox.warning(self, "خطا", "حداقل یک کاربر باید باقی بماند.")
            return
        if QMessageBox.question(
            self, "حذف کاربر", f"کاربر «{u.get('username')}» حذف شود؟"
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
                "فعال" if u.get("is_active") else "غیرفعال"))
            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(2, 2, 2, 2)
            edit_btn = QPushButton("✎")
            edit_btn.setObjectName("Secondary")
            edit_btn.setFixedWidth(40)
            edit_btn.clicked.connect(lambda _, uu=u: self._edit_user(uu))
            del_btn = QPushButton("🗑")
            del_btn.setObjectName("Danger")
            del_btn.setFixedWidth(40)
            del_btn.clicked.connect(lambda _, uu=u: self._delete_user(uu))
            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            self.table.setCellWidget(r, 4, actions)
