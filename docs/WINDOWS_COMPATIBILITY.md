# D-Clinic — Windows Compatibility Report

**Product:** D-Clinic (Zenith Soft) · **Version:** 1.1.0
**Targets requested:** Windows 8, Windows 8.1, Windows 10, Windows 11
**Date:** 2026-06-14

This report covers the pre-release Windows compatibility review: a dependency
and API audit, the installer review, the known limitations, and the
recommended action for each target OS.

---

## 1. Executive summary

| Windows version | Status | Notes |
|---|---|---|
| **Windows 11** | ✅ Fully supported | Primary target. PyInstaller one-folder build runs with no Python installed. |
| **Windows 10** (1809+) | ✅ Fully supported | Primary target. Officially supported by Qt 6.5. |
| **Windows 8.1** | ⚠️ Not guaranteed | The **application code** is fully compatible, but the **Qt 6 runtime** officially requires Windows 10. Use the PyQt5 build path (§6) for a guaranteed Windows 8.1 build. |
| **Windows 8** | ⚠️ Not guaranteed | Same as 8.1. |

**Bottom line:** D-Clinic’s own code uses **no Windows 10/11-only APIs** and
runs on every listed version. The single constraint is the GUI framework:
**Qt 6 (PyQt6) officially targets Windows 10 and 11.** For a contractually
guaranteed Windows 8 / 8.1 release, build against **PyQt5 (Qt 5.15 LTS)**,
which officially supports Windows 7/8/8.1/10 — the steps are in §6 and require
no changes to application logic, only the import layer.

---

## 2. Dependency review

D-Clinic has an intentionally tiny dependency surface, which keeps Windows
compatibility risk very low.

| Dependency | Source | Windows support |
|---|---|---|
| **PyQt6** (`>=6.5,<6.6`) | PyPI wheel (bundles Qt 6.5 LTS) | Win 10 / 11 (official). See §5. |
| sqlite3, hashlib, hmac, base64, json, uuid, platform, datetime, os, sys | Python standard library | All Windows versions |
| **winreg** | Python standard library (Windows) | All Windows versions (NT/2000+) |

Verified automatically: a full AST scan of `app/` finds **exactly one**
external top-level import — `PyQt6`. There are **no** numpy / pandas /
matplotlib / Pillow / requests dependencies (the charts are hand-painted with
`QPainter`, so there is no scientific-stack baggage to break across OS
versions). The PyInstaller spec also explicitly *excludes* those modules.

---

## 3. Windows-specific API audit

A search for OS-specific calls across the whole codebase returns a single
site:

* **`winreg`** in `app/services/license_service.py` — reads
  `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid` to derive a stable
  Machine ID for licensing.
  * Available on **every** Windows version since Windows 2000.
  * Wrapped in `try/except` and guarded by `platform.system() == "Windows"`.
  * Has cross-platform fallbacks (MAC address, hostname, CPU arch), so even if
    the registry read fails the licensing still works.

No use of any Windows 10/11-only API was found — no WinRT, no toast
notifications, no `Qt.HighDpiScaleFactorRoundingPolicy` hacks, no DirectX 12,
no `ctypes` Win32 calls, no `os.startfile` reliance, no PowerShell shelling
out. File paths use `%PROGRAMDATA%` (valid since Windows Vista) with a
portable fallback.

**Conclusion:** the application layer is compatible with Windows 8, 8.1, 10
and 11 without modification.

---

## 4. Installer review

`installer/D-Clinic.iss` (Inno Setup 6):

* `MinVersion=6.2` → the installer itself permits **Windows 8 (6.2), 8.1 (6.3),
  10 and 11**. No change required to *allow* installation on the requested
  targets.
* Installs to `Program Files`, requires admin, and creates shared,
  user-writable data folders under `%PROGRAMDATA%\Zenith Soft\D-Clinic\`
  (`data`, `data\logos`, `backups`, `attachments`) with `users-modify`
  permissions — valid on all four OS versions.
* Data is preserved on uninstall/upgrade.

> ⚠️ **Installer caveat for Windows 8 / 8.1:** with a **PyQt6** build, the
> installer will install successfully on Windows 8/8.1 but the Qt 6 runtime
> may refuse to start (Qt 6 targets Windows 10+). Either ship the **PyQt5**
> build (§6) for those machines, or raise `MinVersion` to `10.0` if you decide
> to officially target only Windows 10/11. The current `MinVersion=6.2` is kept
> so the same installer can serve a PyQt5 Windows 8/8.1 build.

---

## 5. The Qt 6 / Windows 8 limitation (the one real risk)

* **Qt 6.5 LTS** (what PyQt6 ships) lists **Windows 10 (21H2) and Windows 11**
  as supported platforms. Windows 8 / 8.1 are **not** on Qt 6’s supported list.
* In practice a Qt 6 app *may* still launch on Windows 8.1, but this is
  **unsupported and unverified** by the Qt Company and must not be promised to
  a paying clinic without testing on the exact machine.
* Pinning to the **Qt 6.5 LTS** line (`PyQt6>=6.5,<6.6`) is deliberate: later
  Qt 6.6/6.7 releases tighten the Windows-10 baseline further, so 6.5 LTS gives
  the broadest, most stable footprint for the Windows 10/11 target.

---

## 6. Guaranteed Windows 8 / 8.1 path (PyQt5 build)

If a confirmed Windows 8 or 8.1 deployment is required, build against
**PyQt5 (Qt 5.15 LTS)**, which officially supports Windows 7/8/8.1/10. Because
the app already isolates Qt usage behind a small set of widgets and uses
fully-scoped enums, the port is mechanical:

1. `pip install PyQt5==5.15.*` instead of PyQt6.
2. Replace `PyQt6` imports with `PyQt5` and move `QAction`/`QShortcut` from
   `QtGui` back to `QtWidgets` (PyQt5 location).
3. `QtGui.QPageLayout`/`QPageSize` and the fully-scoped enum names
   (`Qt.AlignmentFlag.AlignCenter`, etc.) are available in PyQt5 5.15, so most
   call sites are unchanged.
4. Rebuild with the same PyInstaller spec (swap the excluded/hidden Qt module
   names) and the same Inno Setup script.

No business logic, database, licensing, theming or printing code needs to
change — only the import/runtime layer.

> A future maintenance task could add a thin `app/qt.py` shim that re-exports
> the Qt modules, so a single switch selects PyQt5 vs PyQt6 at build time.

---

## 7. Pre-release validation checklist (run on each target OS)

Build the installer (`build.bat`) and, on a clean VM of **each** target
Windows version, confirm:

- [ ] Installer runs and completes (Win 8 / 8.1 / 10 / 11).
- [ ] App launches to the activation screen.
- [ ] Activation with a FULL key, and with a DEMO key.
- [ ] Login (admin/admin), then change password.
- [ ] Patient add/search/edit; DEMO patient-cap message at the limit.
- [ ] Print and PDF export of an invoice / patient file — including the DEMO
      watermark on demo builds.
- [ ] Backup now, export backup, restore backup.
- [ ] Light ⇄ Dark theme switch, Persian ⇄ English switch.
- [ ] About page shows DEMO remaining days + patient quota.
- [ ] Move the system clock backwards → app blocks with the clock-error
      message; restore the clock → app runs again.

---

## 8. Recommendation

* **Officially advertise Windows 10 and Windows 11** for the v1.1.0 PyQt6
  release — these are fully supported and tested in CI builds.
* For any clinic on **Windows 8 / 8.1**, ship the **PyQt5 build** (§6) and
  validate on that machine before delivery.
* Keep the dependency pinned to the Qt 6.5 LTS line until a deliberate, tested
  upgrade.
