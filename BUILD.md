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

```bash
pip install pyinstaller

pyinstaller --noconfirm --windowed --name D-Clinic ^
    --add-data "app/resources/styles.qss;app/resources" ^
    main.py
```

> On Linux/macOS replace the `;` separator with `:` in `--add-data` and
> use `\` line continuation instead of `^`:
> ```bash
> pyinstaller --noconfirm --windowed --name D-Clinic \
>     --add-data "app/resources/styles.qss:app/resources" \
>     main.py
> ```

Results:
- One-folder build: `dist/D-Clinic/D-Clinic.exe` (portable folder)
- For a single-file build add `--onefile` (slower startup).

Optional: add an application icon with `--icon assets/app.ico`.

The produced executable is fully **offline** and stores its data
(`data/`, `backups/`, `attachments/`) next to the `.exe`.

---

## 4. Database schema

The full SQLite schema (tables, relationships, indexes and seed data)
is defined in **`app/database/schema.py`** and is created automatically
on first run.

Tables: `clinics`, `users`, `patients`, `treatments`, `service_prices`,
`visits`, `attachments`, `payments`, `invoices`, `invoice_items`,
`backups`.
