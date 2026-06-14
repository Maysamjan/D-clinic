"""D-Clinic — Desktop Dental Clinic Management System.

Entry point. Initialises the database, applies the RTL theme, runs the
daily automatic backup and shows the login screen followed by the main
window.
"""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication

from app import config
from app.database import schema
from app.services import backup_service
from app.utils import helpers


class Application:
    """Owns the QApplication lifecycle and window switching."""

    def __init__(self):
        config.ensure_dirs()
        schema.init_db()
        try:
            backup_service.auto_backup_if_needed()
        except Exception:  # noqa: BLE001 — never block startup on backup
            pass

        from app.services import i18n
        from app.models import clinic as clinic_model
        i18n.set_language(clinic_model.get_language())

        self.app = QApplication(sys.argv)
        self.app.setApplicationName(config.APP_NAME)
        import os as _os
        if _os.path.isfile(config.ICON_FILE):
            self.app.setWindowIcon(QIcon(config.ICON_FILE))
        self._apply_direction()
        family = helpers.load_fonts()
        font = QFont(family, 11)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        self.app.setFont(font)
        self.app.setStyleSheet(helpers.load_stylesheet())

        self.login_window = None
        self.main_window = None
        self.activation_window = None

    def _apply_direction(self):
        from app.services import i18n
        self.app.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if i18n.is_rtl()
            else Qt.LayoutDirection.LeftToRight)

    def run(self) -> int:
        self._start()
        return self.app.exec()

    def _start(self):
        """Require a valid product-key activation before anything else."""
        from app.services import license_service as lic

        if not lic.is_activated():
            self._show_activation()
            return

        st = lic.status()
        if st["reason"] == "clock_rollback":
            # The system clock was moved backwards — block until it is fixed.
            self._block_clock_rollback()
            return
        if not st["ok"]:
            # Signature-valid but expired (DEMO) — let them enter a renewal key.
            self._show_activation(reason=st["reason"])
            return

        self._ensure_registration()
        self._show_login()

    def _block_clock_rollback(self):
        from PyQt6.QtWidgets import QMessageBox
        from app.services.i18n import t
        QMessageBox.critical(
            None, config.BRAND + " — " + t("خطای ساعت سیستم"),
            t("تاریخ سیستم به عقب تغییر کرده است.\n\n"
              "برای جلوگیری از دور زدن محدودیت جواز، اجرای برنامه متوقف شد. "
              "لطفاً تاریخ و ساعت ویندوز را به زمان درست تنظیم کنید و دوباره "
              "برنامه را باز کنید."))
        self.app.quit()

    def _ensure_registration(self):
        """Collect clinic details once, after the machine is licensed."""
        from app.models import clinic as clinic_model
        if clinic_model.is_registered():
            return
        from app.ui.activation import RegistrationDialog
        RegistrationDialog().exec()

    def _show_activation(self, reason: str = ""):
        from app.ui.activation import ActivationWindow

        self.activation_window = ActivationWindow(reason=reason)
        self.activation_window.activated.connect(self._on_activated)
        self.activation_window.show()

    def _on_activated(self):
        if self.activation_window is not None:
            self.activation_window.close()
            self.activation_window = None
        self._ensure_registration()
        self._show_login()

    def _show_login(self):
        from app.ui.login import LoginWindow

        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None
        self.login_window = LoginWindow()
        self.login_window.logged_in.connect(self._show_main)
        self.login_window.show()

    def _show_main(self, _user):
        from app.ui.main_window import MainWindow

        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None
        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None
        self.main_window = MainWindow(
            on_logout=self._show_login, on_relaunch=self._relaunch)
        self.main_window.show()

    def _relaunch(self):
        """Rebuild the main window after a language change."""
        from app.services import i18n, session
        from app.models import clinic as clinic_model
        i18n.set_language(clinic_model.get_language())
        self._apply_direction()
        self.app.setStyleSheet(helpers.load_stylesheet())
        if session.current_user:
            self._show_main(session.current_user)


def main() -> int:
    return Application().run()


if __name__ == "__main__":
    sys.exit(main())
