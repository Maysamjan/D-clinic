# Build & Packaging Instructions — D-Clinic

This document explains how to run the project and build a standalone
Windows executable.

---

## 1. Run from source (any OS)

```bash
# 1) create / activate a virtual environment (recommended)
python -m venv .venv
#   Windows:
.venv\Scripts\activate
#   Linux / macOS:
source .venv/bin/activate

# 2) install dependencies
pip install -r requirements.txt

# 3) launch the application
python main.py
```

Default login — **username:** `admin` · **password:** `admin`
(change it from the *Users* page after first login).

The app creates these folders next to the project on first run:
`data/` (SQLite database + logos), `backups/`, `attachments/`.

---

## 2. Use the included sample database (optional)

A pre-populated demo database is provided in `sample/sample.db`
(8 patients with visits, payments and invoices) and a matching backup in
`sample/backup_auto_*.db`.

To start the app with the sample data:

```bash
mkdir -p data            # Windows: md data
copy sample\sample.db data\dclinic.db     # Windows
cp    sample/sample.db data/dclinic.db    # Linux / macOS
python main.py
```

Or simply launch the app, open **Settings → Restore**, and choose
`sample/backup_auto_*.db`.

---

## 3. Build the production .exe + installer (Windows)

The build is driven by a **PyInstaller spec** (`D-Clinic.spec`) and an
**Inno Setup script** (`installer/D-Clinic.iss`), tied together by
`build.bat`.

> **Before building — set your company details.** Open `app/config.py` and
> edit `BRAND`, `BRAND_SLOGAN`, `BRAND_PHONE`, `BRAND_EMAIL` (the phone and
> email shown on the login screen are placeholders). After changing the
> brand letters, regenerate the logo/icon with `python tools/make_logo.py`.

### One command — `build.bat`

On a Windows machine with Python installed, just run:

```bat
build.bat
```

It will:
1. install/upgrade PyInstaller and the requirements,
2. clean old `build/` and `dist/`,
3. build the app from `D-Clinic.spec`  → **`dist\D-Clinic\D-Clinic.exe`**,
4. if **Inno Setup 6** is installed, compile the installer
   → **`installer\Output\D-Clinic-Setup-1.1.0.exe`**.

(If Inno Setup isn't found it simply skips step 4 and you can still ship the
portable `dist\D-Clinic\` folder.)

### What the spec bundles

`D-Clinic.spec` produces a **one-folder** build (faster startup and far fewer
"missing resource" problems than one-file) and ships everything the app needs
so it runs on a **clean Windows PC with no Python installed**:

| Bundled | From |
|---|---|
| App icon (`icon.ico`) + window icon (`icon.png`) | `assets/` |
| **ZS** brand logo (`logo.png`) | `assets/` |
| Vazirmatn RTL/UI fonts | `assets/fonts/` |
| Qt stylesheet | `app/resources/styles.qss` |
| License-activation component (`winreg`) | bundled on Windows |
| Print/PDF support (`QtPrintSupport`) | hidden import |

The spec also embeds Windows file metadata via `version_info.txt`
(Company **Zenith Soft**, Product **D-Clinic**, Description **Dental Clinic
Management System**, Version **1.1.0**, Copyright **Zenith Soft**) — visible
in the .exe's *Properties → Details* tab.

### Manual build (without the script)

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean D-Clinic.spec
"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" installer\D-Clinic.iss
```

### The installer

Compiling `installer/D-Clinic.iss` with Inno Setup 6 produces
**`installer\Output\D-Clinic-Setup-1.1.0.exe`**, which:

- installs into **Program Files** (`C:\Program Files\D-Clinic`),
- creates a **Desktop** shortcut (optional checkbox) and a **Start Menu**
  shortcut,
- creates the shared, user-writable data folders under
  `C:\ProgramData\Zenith Soft\D-Clinic\` (`data`, `data\logos`, `backups`,
  `attachments`),
- offers to **launch D-Clinic** when setup finishes,
- **preserves** all patient data on uninstall / upgrade (only the program
  files in Program Files are removed).

### Where data is stored

Because Program Files is not writable by standard users, the installed app
keeps its database, backups and attachments in a shared location that every
Windows account on the clinic PC can use:

```
C:\ProgramData\Zenith Soft\D-Clinic\
    data\dclinic.db
    backups\
    attachments\
```

(When you run from source it still uses the project folder, and a portable
build with no `%PROGRAMDATA%` falls back to the folder next to the `.exe`.)

### Supported Windows versions

D-Clinic 1.1.0 officially supports **Windows 10 and Windows 11** only
(`MinVersion=10.0` in the `.iss`; Windows 8/8.1 are not supported because the
Qt 6 runtime targets Windows 10+).

> **Always build with `build.bat`**, which uses a **clean virtual environment**
> and the **pinned, matched** PyQt6 packages (`PyQt6==6.6.1`,
> `PyQt6-Qt6==6.6.1`, `PyQt6-sip==13.6.0`). A mismatch between `PyQt6` and
> `PyQt6-Qt6` is what causes the launch error *"DLL load failed while importing
> QtCore: The specified procedure could not be found."* — see
> `docs/WINDOWS_COMPATIBILITY.md`.

**Run the produced `D-Clinic-Setup-1.1.0.exe` once on a clean Windows 10 and a
clean Windows 11 machine** to confirm the full install → launch → activation →
print flow before commercial release.

---

## 4. Database schema

The full SQLite schema (tables, relationships, indexes and seed data)
is defined in **`app/database/schema.py`** and is created automatically
on first run.

Tables: `clinics`, `users`, `patients`, `treatments`, `service_prices`,
`visits`, `attachments`, `payments`, `invoices`, `invoice_items`,
`backups`.
