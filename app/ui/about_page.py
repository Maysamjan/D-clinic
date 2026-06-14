"""About page — product, version, license and support information."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
)

from .. import config
from ..models import clinic as clinic_model
from ..services import license_service as lic
from ..services.i18n import t


class AboutPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(16)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        root.addWidget(self._build_header_card())
        root.addWidget(self._build_info_card())
        root.addWidget(self._build_support_card())
        root.addStretch(1)

    # -- cards ------------------------------------------------------------
    def _build_header_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        lay = QHBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(18)

        logo = QLabel()
        if os.path.isfile(config.LOGO_FILE):
            logo.setPixmap(QPixmap(config.LOGO_FILE).scaled(
                84, 84, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        lay.addWidget(logo)

        text = QVBoxLayout()
        text.setSpacing(3)
        name = QLabel(config.APP_NAME)
        name.setStyleSheet("font-size:26px; font-weight:bold; color:#0B2A33;")
        brand = QLabel(config.BRAND)
        brand.setStyleSheet("font-size:15px; color:#0E9F8E; font-weight:600;")
        slogan = QLabel(t(config.BRAND_SLOGAN))
        slogan.setStyleSheet("color:#64748b; font-size:13px;")
        slogan.setWordWrap(True)
        ver = QLabel(t("نسخه برنامه") + " " + config.APP_VERSION)
        ver.setStyleSheet("color:#46515F; font-size:13px; margin-top:4px;")
        text.addWidget(name)
        text.addWidget(brand)
        text.addWidget(slogan)
        text.addWidget(ver)
        lay.addLayout(text, 1)
        return card

    def _row(self, grid: QGridLayout, r: int, label: str, value: str,
             value_color: str = "#111B27"):
        cap = QLabel(label)
        cap.setStyleSheet("color:#64748b; font-size:13px;")
        val = QLabel(value)
        val.setStyleSheet(
            f"color:{value_color}; font-weight:bold; font-size:14px;")
        val.setWordWrap(True)
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        grid.addWidget(cap, r, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(val, r, 1)

    def _build_info_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(12)
        title = QLabel(t("اطلاعات نرم‌افزار و جواز"))
        title.setObjectName("CardTitle")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(1, 1)

        clinic = clinic_model.get()
        activated = lic.is_activated()
        status_text = t("فعال (دارای جواز)") if activated else t("فعال نشده")
        status_color = "#0A8F60" if activated else "#C0344E"

        self._row(grid, 0, t("محصول"), f"{config.APP_NAME} — {config.BRAND}")
        self._row(grid, 1, t("نسخه برنامه"), config.APP_VERSION)
        self._row(grid, 2, t("وضعیت جواز"), status_text, status_color)
        self._row(grid, 3, t("کلینیک دارای جواز"),
                  clinic.get("name") or "—")
        if clinic.get("owner_name"):
            self._row(grid, 4, t("داکتر / مالک"), clinic.get("owner_name"))
        self._row(grid, 5, t("شناسه دستگاه"), lic.machine_id_display())
        lay.addLayout(grid)
        return card

    def _build_support_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(10)
        title = QLabel(t("پشتیبانی"))
        title.setObjectName("CardTitle")
        lay.addWidget(title)
        contact = QLabel(
            f"📞 {config.BRAND_PHONE}  ✉ {config.BRAND_EMAIL}")
        contact.setStyleSheet("font-size:14px; color:#16202E; font-weight:600;")
        contact.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(contact)
        note = QLabel(t("برای دریافت پشتیبانی، تمدید جواز یا گزارش مشکل با ما در تماس شوید."))
        note.setStyleSheet("color:#64748b; font-size:12px;")
        note.setWordWrap(True)
        lay.addWidget(note)
        copyright_lbl = QLabel("© " + config.BRAND + " · " + config.APP_NAME
                               + " " + config.APP_VERSION)
        copyright_lbl.setStyleSheet("color:#94A3B8; font-size:11px; margin-top:6px;")
        lay.addWidget(copyright_lbl)
        return card

    def refresh(self):
        pass
