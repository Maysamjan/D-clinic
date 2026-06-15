"""Login window."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget
)

from .. import config
from ..models import user as user_model
from ..services import session, theme
from ..services.i18n import t


class LoginWindow(QWidget):
    """Standalone login screen; emits ``logged_in`` with the user dict."""

    logged_in = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(config.BRAND + " — " + t("ورود"))
        self.resize(960, 620)
        self._build()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left branding panel
        brand = QFrame()
        brand.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 #0C2A33, stop:1 #11A593);"
        )
        bl = QVBoxLayout(brand)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.setSpacing(8)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.isfile(config.LOGO_FILE):
            pix = QPixmap(config.LOGO_FILE).scaled(
                150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("ZS")
            logo.setStyleSheet("color:#fff; font-size:72px; font-weight:bold;")

        name = QLabel(config.BRAND)
        name.setStyleSheet("color:#ffffff; font-size:38px; font-weight:bold;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        slogan = QLabel(t(config.BRAND_SLOGAN))
        slogan.setStyleSheet("color:#CFEFEA; font-size:15px;")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan.setWordWrap(True)

        contact = QLabel(f"📞 {config.BRAND_PHONE}    ✉ {config.BRAND_EMAIL}")
        contact.setStyleSheet("color:#9FD8D1; font-size:13px; margin-top:14px;")
        contact.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contact.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)

        bl.addWidget(logo)
        bl.addWidget(name)
        bl.addWidget(slogan)
        bl.addWidget(contact)

        # Right login form
        right = QFrame()
        right.setStyleSheet("background-color:" + theme.color("bg") + ";")
        rl = QVBoxLayout(right)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setMaximumWidth(360)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(15, 41, 66, 50))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(14)

        title = QLabel(t("ورود به سیستم"))
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel(t("لطفاً نام کاربری و رمز عبور خود را وارد کنید"))
        hint.setObjectName("LoginSub")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        self.username = QLineEdit()
        self.username.setPlaceholderText(t("نام کاربری"))
        self.username.setMinimumHeight(42)
        self.password = QLineEdit()
        self.password.setPlaceholderText(t("رمز عبور"))
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMinimumHeight(42)

        login_btn = QPushButton(t("ورود"))
        login_btn.setMinimumHeight(46)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet(
            "QPushButton { background-color:#0E9F8E; color:#ffffff; border:none;"
            " border-radius:10px; font-weight:700; font-size:16px; }"
            "QPushButton:hover { background-color:#0C8E7F; }"
            "QPushButton:pressed { background-color:#0A7A6D; }")
        login_btn.clicked.connect(self._attempt_login)

        self.username.returnPressed.connect(self.password.setFocus)
        self.password.returnPressed.connect(self._attempt_login)

        cl.addWidget(title)
        cl.addWidget(hint)
        cl.addSpacing(6)
        cl.addWidget(QLabel(t("نام کاربری")))
        cl.addWidget(self.username)
        cl.addWidget(QLabel(t("رمز عبور")))
        cl.addWidget(self.password)
        cl.addSpacing(8)
        cl.addWidget(login_btn)

        hint2 = QLabel(t("ورود پیش‌فرض مدیر:  admin / admin"))
        hint2.setObjectName("LoginHint")
        hint2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addSpacing(4)
        cl.addWidget(hint2)

        rl.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

        outer.addWidget(right, 1)
        outer.addWidget(brand, 1)

        self.username.setFocus()

    def _attempt_login(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, t("خطا"), t("نام کاربری و رمز عبور را وارد کنید."))
            return
        user = user_model.authenticate(username, password)
        if user is None:
            QMessageBox.critical(self, t("خطای ورود"),
                                 t("نام کاربری یا رمز عبور اشتباه است."))
            self.password.clear()
            self.password.setFocus()
            return
        session.login(user)
        self.logged_in.emit(user)
