"""Application configuration, paths and constants.

All data is stored locally inside the application directory so the program
is fully portable and works completely offline. On Windows the application
folder usually lives next to the executable; here we anchor everything to
the project root.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Base directories
# ---------------------------------------------------------------------------

def _base_dir() -> str:
    """Return the directory that holds the application data.

    When frozen with PyInstaller we store data next to the executable,
    otherwise next to the source tree.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resource_dir() -> str:
    """Directory holding read-only bundled resources (assets, fonts).

    When frozen with PyInstaller these live in the temporary extraction
    directory (``sys._MEIPASS``); from source they live in the project root.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    return meipass if meipass else _base_dir()


# Writable data lives next to the executable / project so it survives updates.
BASE_DIR = _base_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "dclinic.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
LOGO_DIR = os.path.join(DATA_DIR, "logos")

# Read-only resources (bundled into the executable).
RESOURCE_DIR = _resource_dir()
ASSETS_DIR = os.path.join(RESOURCE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
LOGO_FILE = os.path.join(ASSETS_DIR, "logo.png")     # brand logo (ZS badge)
ICON_FILE = os.path.join(ASSETS_DIR, "icon.png")     # window/app icon

# Primary UI font family (bundled, see assets/fonts).
FONT_FAMILY = "Vazirmatn"

# How many automatic daily backups to keep before rotating out the oldest.
MAX_AUTO_BACKUPS = 14

# Default currency label used across invoices and reports.
CURRENCY = "AFN"

# Application metadata
APP_NAME = "D-Clinic"
APP_TITLE = "سیستم مدیریت کلینیک دندانپزشکی"  # Dental Clinic Management System

# ---------------------------------------------------------------------------
# Vendor / company branding shown on the login, sidebar and activation screens.
# ⬇️  EDIT THESE THREE LINES with your real company details before building.
# ---------------------------------------------------------------------------
BRAND = "Zenith Soft"
BRAND_SLOGAN = "راهکار هوشمند مدیریت کلینیک دندانپزشکی"
BRAND_PHONE = "+93 700 000 000"
BRAND_EMAIL = "info@zenithsoft.com"


def ensure_dirs() -> None:
    """Create the writable directories the application relies on."""
    for path in (DATA_DIR, BACKUP_DIR, ATTACHMENTS_DIR, LOGO_DIR):
        os.makedirs(path, exist_ok=True)


# Role identifiers ----------------------------------------------------------
ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_RECEPTIONIST = "receptionist"

ROLE_LABELS = {
    ROLE_ADMIN: "مدیر",
    ROLE_DOCTOR: "داکتر",
    ROLE_RECEPTIONIST: "پذیرش",
}
