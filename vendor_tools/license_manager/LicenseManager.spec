# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Zenith Soft License Manager (VENDOR-ONLY tool).

Builds dist/LicenseManager/LicenseManager.exe — a one-folder build.

IMPORTANT: this spec deliberately does NOT bundle the private key or the
generated_licenses/ history. Those live next to the executable at runtime and
must never be shipped to customers.

Build (from this folder):  pyinstaller --noconfirm LicenseManager.spec
"""

import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None
ROOT = os.path.abspath(os.getcwd())

# Optional icon — reuse D-Clinic's app icon if present.
_icon = os.path.join(ROOT, "..", "..", "assets", "icon.ico")
icon = _icon if os.path.isfile(_icon) else None

# Bundle the COMPLETE PyQt6 runtime (all Qt DLLs + the platforms\qwindows.dll
# plugin) so the tool runs on a clean Windows 10/11 PC. Together with the
# matched PyQt6 / PyQt6-Qt6 versions in requirements.txt this avoids the
# "DLL load failed while importing QtCore" launch error.
pyqt_datas, pyqt_binaries, pyqt_hidden = collect_all("PyQt6")

a = Analysis(
    ["license_manager.py"],
    pathex=[ROOT],
    binaries=pyqt_binaries,
    datas=pyqt_datas,
    hiddenimports=pyqt_hidden + [
        "ed25519", "licensing_core", "history_db",
        "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "pkgutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "scipy", "pandas", "PIL",
        "PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets", "PyQt6.QtQml",
        "PyQt6.QtQuick", "PyQt6.QtMultimedia", "PyQt6.QtBluetooth",
        "PyQt6.Qt3DCore",
    ],
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
    name="LicenseManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LicenseManager",
)
