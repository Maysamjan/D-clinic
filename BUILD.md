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

## 3. Build a standalone Windows .exe (PyInstaller)

### Easiest — use the build script

On Windows just double-click / run **`build.bat`**, which performs all the
steps below and produces `dist/D-Clinic/D-Clinic.exe`:

```bat
build.bat
```

### Manual command

```bash
pip install pyinstaller

pyinstaller --noconfirm --windowed --name D-Clinic ^
    --icon assets/icon.ico ^
    --add-data "app/resources/styles.qss;app/resources" ^
    --add-data "assets;assets" ^
    main.py
```

> On Linux/macOS replace the `;` separator with `:` in `--add-data` and
> use `\` line continuation instead of `^`:
> ```bash
> pyinstaller --noconfirm --windowed --name D-Clinic \
>     --icon assets/icon.ico \
>     --add-data "app/resources/styles.qss:app/resources" \
>     --add-data "assets:assets" \
>     main.py
> ```

> The bundled **Vazirmatn** font lives in `assets/fonts` and the **ZS**
> brand logo / app icon live in `assets/` — the `--add-data "assets;assets"`
> flag ships them inside the executable so the UI, login branding and
> printed documents look identical on every machine. The
> `--icon assets/icon.ico` flag sets the Windows taskbar / desktop icon.

Results:
- One-folder build: `dist/D-Clinic/D-Clinic.exe` (portable folder)
- For a single-file build add `--onefile` (slower startup).

The produced executable is fully **offline** and stores its data
(`data/`, `backups/`, `attachments/`) next to the `.exe`.

> **Before building — set your company details.** Open `app/config.py` and
> edit `BRAND`, `BRAND_SLOGAN`, `BRAND_PHONE` and `BRAND_EMAIL` (the phone
> and email shown on the login screen are placeholders). To regenerate the
> logo/icon after changing the brand letters, run
> `python tools/make_logo.py`.

---

## 4. Database schema

The full SQLite schema (tables, relationships, indexes and seed data)
is defined in **`app/database/schema.py`** and is created automatically
on first run.

Tables: `clinics`, `users`, `patients`, `treatments`, `service_prices`,
`visits`, `attachments`, `payments`, `invoices`, `invoice_items`,
`backups`.
