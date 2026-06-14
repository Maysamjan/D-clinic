# -*- mode: python ; coding: utf-8 -*-
"""Production PyInstaller spec for D-Clinic (Zenith Soft).

One-folder build (faster startup and more reliable resource loading than
one-file): the executable is produced at ``dist/D-Clinic/D-Clinic.exe`` and
ships with every asset it needs so it runs on a clean Windows machine that
has **no Python installed**.

Build:   pyinstaller --noconfirm D-Clinic.spec
"""

import os
import sys

block_cipher = None
ROOT = os.path.abspath(os.getcwd())


def collect_tree(src_root, dest_root):
    """Return (source, dest) tuples for every file under ``src_root``."""
    items = []
    for cur, _dirs, files in os.walk(src_root):
        for name in files:
            full = os.path.join(cur, name)
            rel = os.path.relpath(cur, src_root)
            dest = dest_root if rel == "." else os.path.join(dest_root, rel)
            items.append((full, dest))
    return items


# --- Bundled read-only resources ------------------------------------------
#  * Stylesheet (QSS)            -> app/resources
#  * Brand logo + app icons      -> assets
#  * Vazirmatn fonts (RTL + UI)  -> assets/fonts
datas = [("app/resources/styles.qss", "app/resources")]
datas += collect_tree("assets", "assets")

# QtPrintSupport powers the printing/PDF features. winreg is imported lazily
# inside the licensing module (Windows only) so it is bundled there to keep the
# activation component intact.
hiddenimports = ["PyQt6.QtPrintSupport"]
if sys.platform.startswith("win"):
    hiddenimports.append("winreg")

# Trim modules the app never uses to shrink the build and speed up startup.
excludes = [
    "tkinter", "matplotlib", "numpy", "scipy", "pandas", "PIL",
    "pytest", "setuptools", "pip",
    "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets", "PyQt6.QtWebEngine",
    "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtMultimedia", "PyQt6.QtBluetooth",
    "PyQt6.Qt3DCore", "PyQt6.QtNetwork", "PyQt6.QtSql", "PyQt6.QtTest",
]

a = Analysis(
    ["main.py"],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="D-Clinic",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # GUI app — no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join("assets", "icon.ico"),
    version="version_info.txt",  # embeds Company / Product / Version metadata
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="D-Clinic",
)
