"""Main application window: sidebar navigation + stacked pages."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget
)

from .. import config
from ..models import clinic as clinic_model
from ..services import session
from ..services.i18n import is_rtl, t
from .appointments_page import AppointmentsPage
from .dashboard import DashboardPage
from .expenses_page import ExpensesPage
from .inventory_page import InventoryPage
from .patient_file import PatientFilePage
from .patients_page import PatientsPage
from .reports_page import ReportsPage
from .salary_page import SalaryPage
from .services_page import ServicesPage
from .settings_page import SettingsPage
from .staff_page import StaffPage
from .users_page import UsersPage


class MainWindow(QMainWindow):
    def __init__(self, on_logout=None, on_relaunch=None):
        super().__init__()
        self._on_logout = on_logout
        self._on_relaunch = on_relaunch
        self.setWindowTitle(config.BRAND + " — " + t(config.APP_TITLE))
        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if is_rtl()
            else Qt.LayoutDirection.LeftToRight)
        self.resize(1280, 800)
        self.setMinimumSize(1000, 600)
        self._nav_buttons: dict[str, QPushButton] = {}
        self._build()
        self._go("dashboard")

    # -- Construction -----------------------------------------------------
    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        rlayout = QVBoxLayout(right)
        rlayout.setContentsMargins(0, 0, 0, 0)
        rlayout.setSpacing(0)
        rlayout.addWidget(self._build_header())

        self.stack = QStackedWidget()
        rlayout.addWidget(self.stack, 1)
        root.addWidget(right, 1)

        self._build_pages()

    def _build_sidebar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("Sidebar")
        bar.setFixedWidth(258)
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(16, 22, 16, 20)
        lay.setSpacing(7)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        import os as _os
        logo_lbl = QLabel()
        if _os.path.isfile(config.LOGO_FILE):
            from PyQt6.QtGui import QPixmap
            logo_lbl.setPixmap(QPixmap(config.LOGO_FILE).scaled(
                34, 34, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        brand = QLabel(config.BRAND)
        brand.setObjectName("BrandTitle")
        brand_row.addWidget(logo_lbl)
        brand_row.addWidget(brand, 1)
        sub = QLabel(t("مدیریت کلینیک دندانپزشکی"))
        sub.setObjectName("BrandSub")
        lay.addLayout(brand_row)
        lay.addWidget(sub)
        lay.addSpacing(14)
        sep = QFrame()
        sep.setObjectName("NavSep")
        sep.setFrameShape(QFrame.Shape.HLine)
        lay.addWidget(sep)
        lay.addSpacing(10)

        # Scrollable nav area so the menu never overflows on short screens
        nav_scroll = QScrollArea()
        nav_scroll.setObjectName("NavScroll")
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_container = QWidget()
        nav_container.setObjectName("NavScroll")
        nav_lay = QVBoxLayout(nav_container)
        nav_lay.setContentsMargins(0, 0, 0, 0)
        nav_lay.setSpacing(7)
        nav_scroll.setWidget(nav_container)
        lay.addWidget(nav_scroll, 1)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        nav_items = [
            ("dashboard", "🏠", "داشبورد", "dashboard"),
            ("appointments", "🗓", "نوبت‌دهی", "appointments"),
            ("patients", "👥", "مریض‌ها", "patients"),
            ("staff", "🩺", "داکتران و کارمندان", "staff"),
            ("salaries", "💵", "معاشات", "salaries"),
            ("inventory", "📦", "گدام و انبار", "inventory"),
            ("expenses", "🧾", "مصارف و حسابداری", "expenses"),
            ("reports", "📊", "گزارش‌ها", "reports"),
            ("services", "💲", "خدمات و قیمت‌ها", "services"),
            ("users", "🔑", "کاربران", "users"),
            ("settings", "⚙", "تنظیمات", "settings"),
        ]
        for key, icon, label, cap in nav_items:
            if not session.can(cap):
                continue
            btn = QPushButton(f"{icon}  {t(label)}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self._go(k))
            self._nav_group.addButton(btn)
            nav_lay.addWidget(btn)
            self._nav_buttons[key] = btn

        nav_lay.addStretch(1)

        sep2 = QFrame()
        sep2.setObjectName("NavSep")
        sep2.setFrameShape(QFrame.Shape.HLine)
        lay.addWidget(sep2)
        lay.addSpacing(6)
        logout_btn = QPushButton("🚪  " + t("خروج از حساب"))
        logout_btn.setObjectName("NavLogout")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        lay.addWidget(logout_btn)
        return bar

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(74)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(26, 0, 26, 0)
        lay.setSpacing(12)

        self.page_title = QLabel(t("داشبورد"))
        self.page_title.setObjectName("PageTitle")
        lay.addWidget(self.page_title)
        lay.addStretch(1)

        self.clinic_name = QLabel()
        self.clinic_name.setObjectName("ClinicName")
        lay.addWidget(self.clinic_name)
        lay.addSpacing(16)

        user = session.current_user or {}
        role_label = t(config.ROLE_LABELS.get(user.get("role"), ""))
        self.user_chip = QLabel(f"👤 {user.get('full_name') or user.get('username','')} — {role_label}")
        self.user_chip.setObjectName("UserChip")
        lay.addWidget(self.user_chip)

        self._refresh_clinic_name()
        return header

    def _build_pages(self):
        self.pages: dict[str, QWidget] = {}

        self.dashboard = DashboardPage()
        self._add_page("dashboard", self.dashboard)

        if session.can("appointments"):
            self.appointments = AppointmentsPage()
            self.appointments.open_patient.connect(self._open_patient)
            self._add_page("appointments", self.appointments)

        self.patients = PatientsPage()
        self.patients.open_patient.connect(self._open_patient)
        self._add_page("patients", self.patients)

        self.patient_file = PatientFilePage()
        self.patient_file.back.connect(lambda: self._go("patients"))
        self.stack.addWidget(self.patient_file)  # not a nav page

        if session.can("staff"):
            self.staff = StaffPage()
            self._add_page("staff", self.staff)
        if session.can("salaries"):
            self.salaries = SalaryPage()
            self._add_page("salaries", self.salaries)
        if session.can("inventory"):
            self.inventory = InventoryPage()
            self._add_page("inventory", self.inventory)
        if session.can("expenses"):
            self.expenses = ExpensesPage()
            self._add_page("expenses", self.expenses)
        if session.can("reports"):
            self.reports = ReportsPage()
            self._add_page("reports", self.reports)
        if session.can("services"):
            self.services = ServicesPage()
            self._add_page("services", self.services)
        if session.can("users"):
            self.users = UsersPage()
            self._add_page("users", self.users)
        if session.can("settings"):
            self.settings = SettingsPage()
            self.settings.clinic_updated.connect(self._refresh_clinic_name)
            self.settings.data_restored.connect(self._on_data_restored)
            if self._on_relaunch:
                self.settings.language_changed.connect(self._on_relaunch)
            self._add_page("settings", self.settings)

    def _add_page(self, key: str, widget: QWidget):
        self.pages[key] = widget
        self.stack.addWidget(widget)

    # -- Navigation -------------------------------------------------------
    _TITLES = {
        "dashboard": "داشبورد",
        "appointments": "نوبت‌دهی",
        "patients": "مدیریت مریض‌ها",
        "staff": "داکتران و کارمندان",
        "salaries": "معاشات کارمندان",
        "inventory": "گدام و انبار",
        "expenses": "مصارف و حسابداری",
        "reports": "گزارش‌ها",
        "services": "خدمات و قیمت‌ها",
        "users": "مدیریت کاربران",
        "settings": "تنظیمات",
    }

    def _go(self, key: str):
        page = self.pages.get(key)
        if page is None:
            return
        if hasattr(page, "refresh"):
            page.refresh()
        self.stack.setCurrentWidget(page)
        self.page_title.setText(t(self._TITLES.get(key, "")))
        if key in self._nav_buttons:
            self._nav_buttons[key].setChecked(True)

    def _open_patient(self, patient_id: int):
        self.patient_file.load_patient(patient_id)
        self.stack.setCurrentWidget(self.patient_file)
        self.page_title.setText("پرونده مریض")

    # -- Misc -------------------------------------------------------------
    def _refresh_clinic_name(self):
        c = clinic_model.get()
        self.clinic_name.setText(c.get("name") or "")

    def _on_data_restored(self):
        QMessageBox.information(
            self, t("بازیابی"),
            t("اطلاعات بازیابی شد. برنامه به داشبورد بازمی‌گردد."))
        self._refresh_clinic_name()
        self._go("dashboard")

    def _logout(self):
        if QMessageBox.question(
            self, t("خروج"), t("از حساب کاربری خارج می‌شوید؟")
        ) == QMessageBox.StandardButton.Yes:
            session.logout()
            if self._on_logout:
                self._on_logout()
