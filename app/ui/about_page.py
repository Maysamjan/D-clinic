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
from ..services import theme
from ..services.i18n import t
from ..utils import helpers


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
        name.setStyleSheet(
            "font-size:26px; font-weight:bold; color:" + theme.color("text") + ";")
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
             value_color: str | None = None):
        if value_color is None:
            value_color = theme.color("text")
        cap = QLabel(label)
        cap.setStyleSheet("color:" + theme.color("muted") + "; font-size:13px;")
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
        st = lic.status()
        activated = st["activated"]
        status_text = t("فعال (دارای جواز)") if activated else t("فعال نشده")
        status_color = "#0A8F60" if activated else "#C0344E"

        r = 0
        self._row(grid, r, t("محصول"), f"{config.APP_NAME} — {config.BRAND}"); r += 1
        self._row(grid, r, t("نسخه برنامه"), config.APP_VERSION); r += 1
        self._row(grid, r, t("وضعیت جواز"), status_text, status_color); r += 1

        # License type + DEMO details (remaining days, patient usage).
        if activated:
            if st["is_demo"]:
                self._row(grid, r, t("نوع جواز"),
                          t("نسخه آزمایشی (DEMO)"), "#A66617"); r += 1
                days = st["days_remaining"]
                if days is not None:
                    if days < 0:
                        rem_text, rem_color = t("منقضی شده"), "#C0344E"
                    else:
                        rem_text = (helpers.jalali_digits(days) + " "
                                    + t("روز باقی‌مانده"))
                        rem_color = "#0A8F60" if days > 5 else "#A66617"
                    self._row(grid, r, t("اعتبار باقی‌مانده"), rem_text, rem_color)
                    r += 1
                if st["expiry_date"] is not None:
                    self._row(grid, r, t("تاریخ انقضا"),
                              helpers.jalali_date(st["expiry_date"].isoformat()))
                    r += 1
                limit = st["max_patients"] or 0
                if limit > 0:
                    usage = (helpers.jalali_digits(st["patient_count"]) + " / "
                             + helpers.jalali_digits(limit))
                    used_up = st["patient_count"] >= limit
                    self._row(grid, r, t("سهمیه مریض"), usage,
                              "#C0344E" if used_up else "#111B27")
                    r += 1
            else:
                self._row(grid, r, t("نوع جواز"),
                          t("نسخه کامل (FULL)"), "#0A8F60"); r += 1

        self._row(grid, r, t("کلینیک دارای جواز"),
                  clinic.get("name") or "—"); r += 1
        if clinic.get("owner_name"):
            self._row(grid, r, t("داکتر / مالک"), clinic.get("owner_name")); r += 1
        self._row(grid, r, t("شناسه دستگاه"), lic.machine_id_display())
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
        contact.setStyleSheet(
            "font-size:14px; color:" + theme.color("text") + "; font-weight:600;")
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
