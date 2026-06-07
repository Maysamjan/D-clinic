"""D-Clinic — Desktop Dental Clinic Management System.

Entry point. Initialises the database, applies the RTL theme, runs the
daily automatic backup and shows the login screen followed by the main
window.
"""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
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

        self.app = QApplication(sys.argv)
        self.app.setApplicationName(config.APP_NAME)
        self.app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.app.setFont(QFont("Segoe UI", 10))
        self.app.setStyleSheet(helpers.load_stylesheet())

        self.login_window = None
        self.main_window = None

    def run(self) -> int:
        self._show_login()
        return self.app.exec()

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
        self.main_window = MainWindow(on_logout=self._show_login)
        self.main_window.show()


def main() -> int:
    return Application().run()


if __name__ == "__main__":
    sys.exit(main())
