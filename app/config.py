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
    """Return the directory that holds the writable application data.

    When frozen with PyInstaller the program is normally installed under
    ``C:\\Program Files`` where standard users may not write, so the database,
    backups and attachments are kept in a shared, user-writable location
    (``%PROGRAMDATA%\\Zenith Soft\\D-Clinic``) so the clinic database is shared
    by every Windows account on the machine. If ``%PROGRAMDATA%`` is somehow
    unavailable we fall back to the folder next to the executable (portable
    use). From source we store data next to the project tree.
    """
    if getattr(sys, "frozen", False):
        if sys.platform.startswith("win"):
            root = os.environ.get("PROGRAMDATA")
            if root and os.path.isdir(root):
                return os.path.join(root, "Zenith Soft", "D-Clinic")
            return os.path.dirname(sys.executable)
        # Non-Windows frozen build: keep data in the user's home directory.
        return os.path.join(os.path.expanduser("~"), ".d-clinic")
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
APP_VERSION = "1.0.0"
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
