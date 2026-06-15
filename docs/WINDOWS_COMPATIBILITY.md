# D-Clinic — Windows Compatibility Report

**Product:** D-Clinic (Zenith Soft) · **Version:** 1.1.0
**Supported OS:** **Windows 10 and Windows 11** (64-bit)
**Date:** 2026-06-15

> **Windows 8 / 8.1 are NOT supported in this release.** The Qt 6 runtime that
> powers D-Clinic officially targets Windows 10 and 11 only. Earlier drafts
> explored a Windows 8 path; it has been **dropped** so the product has one
> clean, tested, officially supported target.

---

## 1. Supported operating systems

| Windows version | Status |
|---|---|
| **Windows 11** | ✅ Supported |
| **Windows 10** (64-bit, 1809 or newer) | ✅ Supported |
| Windows 8.1 / 8 / 7 | ❌ Not supported |

The Inno Setup installer enforces this with `MinVersion=10.0`, so it will not
install on Windows 8/8.1 or older.

---

## 2. The launch error that was fixed

Some builds failed at startup with:

```
ImportError: DLL load failed while importing QtCore:
The specified procedure could not be found.
```

**Root cause:** a **version mismatch between the two PyQt6 packages** —
`PyQt6` (the Python bindings) and `PyQt6-Qt6` (the actual Qt DLLs). When `pip`
is left unpinned it can install, for example, `PyQt6 6.11.0` against
`PyQt6-Qt6 6.11.1`. The bindings then call a Qt entry point (procedure) that
does not exist in the other version's `Qt6Core.dll`, and Windows reports
*"The specified procedure could not be found."*

**Fix (applied):**

1. **Pin the three PyQt6 packages to one matched Qt version** in
   `requirements.txt`:
   ```
   PyQt6==6.6.1
   PyQt6-Qt6==6.6.1
   PyQt6-sip==13.6.0
   ```
   `PyQt6` and `PyQt6-Qt6` **must** be the same version (6.6.1 here).
2. **Build inside a clean virtual environment** (`build.bat` now creates
   `.venv-build`) so no stray/mismatched Qt DLLs from a global Python leak into
   the build.
3. **Bundle the complete PyQt6 runtime** in `D-Clinic.spec` via
   `collect_all("PyQt6")` — every Qt DLL, the `platforms\qwindows.dll`
   platform plugin, styles and imageformats — and list the core modules
   (`QtCore`, `QtGui`, `QtWidgets`, `QtPrintSupport`) plus `pkgutil` as hidden
   imports so PyInstaller never trims them.

After these changes the bindings and the bundled Qt DLLs are guaranteed to be
the same version, which removes the "specified procedure could not be found"
error.

---

## 3. Dependency review

| Dependency | Pinned | Notes |
|---|---|---|
| **PyQt6** | `==6.6.1` | GUI bindings |
| **PyQt6-Qt6** | `==6.6.1` | Qt 6.6 binaries — **must match PyQt6** |
| **PyQt6-sip** | `==13.6.0` | sip runtime for PyQt6 6.6.x |
| sqlite3, hashlib, hmac, base64, json, uuid, platform, datetime, pkgutil | stdlib | — |
| **winreg** | stdlib (Windows) | Machine-ID registry read; available on Win 10/11 |

A full AST scan of `app/` finds **exactly one** external top-level import —
`PyQt6`. No numpy / pandas / matplotlib / Pillow / requests; the charts are
hand-painted with `QPainter`.

---

## 4. Application-code review

* The only OS-specific call is `winreg` (reads
  `HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid`), available on Windows 10
  and 11, wrapped in `try/except` with cross-platform fallbacks.
* No Windows-11-only APIs, no WinRT, no `ctypes` Win32 calls, no DirectX.
* Data is stored under `%PROGRAMDATA%\Zenith Soft\D-Clinic\`.

---

## 5. Installer

`installer/D-Clinic.iss` (Inno Setup 6):

* `MinVersion=10.0` → installs on **Windows 10 and 11 only**.
* Installs to `Program Files` (admin), with shared, user-writable data folders
  under `%PROGRAMDATA%\Zenith Soft\D-Clinic\` (`data`, `data\logos`, `backups`,
  `attachments`).
* Data is preserved on uninstall/upgrade.
* Output: `installer\Output\D-Clinic-Setup-1.1.0.exe`.

---

## 6. Build & verification steps

Build from a **clean virtual environment** on a Windows 10/11 machine:

```bat
build.bat
```

`build.bat` will: create `.venv-build`, install the pinned requirements +
PyInstaller, assert that `PyQt6` and the Qt runtime versions match, build
`dist\D-Clinic\D-Clinic.exe`, and (if Inno Setup 6 is present) produce
`installer\Output\D-Clinic-Setup-1.1.0.exe`.

Confirm, in order:

- [ ] `python main.py` launches (activation screen appears).
- [ ] `dist\D-Clinic\D-Clinic.exe` launches with **no** QtCore DLL error.
- [ ] Activation (FULL + DEMO), login (admin/admin), patient add/search.
- [ ] Print / PDF export of an invoice and a prescription (with the logo);
      DEMO watermark on demo builds.
- [ ] Backup now, export, restore.
- [ ] Light ⇄ Dark and Persian ⇄ English switches.
- [ ] About page shows DEMO remaining days + patient quota.
- [ ] Clock-rollback is blocked, then runs again once the date is corrected.

Run the `.exe` once on a clean **Windows 10** and a clean **Windows 11**
machine before commercial release.
