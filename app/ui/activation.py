"""Product-key activation screen, shown until the machine is licensed."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
)

from .. import config
from ..services import license_service as lic
from ..services.i18n import t


class ActivationWindow(QWidget):
    """Shown at start-up when the computer is not yet activated."""

    activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(config.BRAND + " — " + t("فعال‌سازی"))
        self.resize(720, 600)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setMaximumWidth(560)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(15, 41, 66, 50))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(34, 30, 34, 30)
        lay.setSpacing(14)

        logo = QLabel("🦷  " + config.BRAND)
        logo.setObjectName("LoginTitle")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel(t("فعال‌سازی نرم‌افزار"))
        title.setStyleSheet("font-size:18px; font-weight:700; color:#0E9F8E;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel(t("این نسخه برای همین کمپیوتر قفل می‌شود. لطفاً «شناسه دستگاه» زیر را "
            "برای فروشنده بفرستید و «کلید محصول» دریافتی را وارد کنید."))
        hint.setObjectName("LoginSub")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)
        lay.addWidget(title)
        lay.addWidget(hint)

        # Machine ID box
        mid_box = QFrame()
        mid_box.setStyleSheet(
            "background:#E3F6F3; border:1px solid #A6DCD5; border-radius:10px;")
        ml = QVBoxLayout(mid_box)
        ml.setContentsMargins(14, 10, 14, 10)
        cap = QLabel(t("شناسه دستگاه شما:"))
        cap.setStyleSheet("color:#0A6B61; font-size:12px; font-weight:600;")
        self.mid_label = QLabel(lic.machine_id_display())
        self.mid_label.setStyleSheet(
            "color:#0A6B61; font-size:18px; font-weight:700;")
        self.mid_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        copy_btn = QPushButton(t("کپی شناسه دستگاه"))
        copy_btn.setObjectName("Secondary")
        copy_btn.clicked.connect(self._copy_mid)
        ml.addWidget(cap)
        ml.addWidget(self.mid_label)
        ml.addWidget(copy_btn)
        lay.addWidget(mid_box)

        lay.addWidget(QLabel(t("کلید محصول:")))
        self.key_input = QPlainTextEdit()
        self.key_input.setPlaceholderText(t("کلید محصول را اینجا وارد یا الصاق کنید ..."))
        self.key_input.setFixedHeight(80)
        lay.addWidget(self.key_input)

        row = QHBoxLayout()
        load_btn = QPushButton(t("بارگذاری فایل کلید (.lic)"))
        load_btn.setObjectName("Secondary")
        load_btn.clicked.connect(self._load_file)
        activate_btn = QPushButton(t("فعال‌سازی"))
        activate_btn.setMinimumHeight(44)
        activate_btn.clicked.connect(self._activate)
        row.addWidget(load_btn)
        row.addWidget(activate_btn, 1)
        lay.addLayout(row)

        root.addWidget(card)

    def _copy_mid(self):
        QGuiApplication.clipboard().setText(lic.machine_id_display())
        QMessageBox.information(self, t("کپی شد"), t("شناسه دستگاه کپی شد."))

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب فایل کلید", "", "License (*.lic);;All files (*.*)")
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    self.key_input.setPlainText(fh.read().strip())
            except OSError as exc:
                QMessageBox.critical(self, "خطا", str(exc))

    def _activate(self):
        key = self.key_input.toPlainText().strip()
        if not key:
            QMessageBox.warning(self, t("خطا"), t("لطفاً کلید محصول را وارد کنید."))
            return
        if lic.activate(key):
            QMessageBox.information(
                self, t("فعال شد"), t("نرم‌افزار با موفقیت فعال شد."))
            self.activated.emit()
        else:
            QMessageBox.critical(
                self, t("کلید نامعتبر"),
                t("کلید محصول برای این کمپیوتر معتبر نیست.\n"
                  "لطفاً شناسه دستگاه را دوباره برای فروشنده بفرستید."))
