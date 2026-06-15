# D-Clinic — Release Notes

## v1.1.0 — Windows compatibility, Dark Mode & DEMO licensing

**Release date:** 2026-06-15 · No breaking changes; existing installs upgrade
automatically on first launch.

### Supported OS — Windows 10 and Windows 11 only
This release officially targets **Windows 10 and Windows 11** (64-bit).
Windows 8 / 8.1 are **not supported** (the Qt 6 runtime targets Windows 10+).

### 1. Windows build fix — QtCore DLL load error
- Fixed the startup crash *"ImportError: DLL load failed while importing
  QtCore: The specified procedure could not be found."* — caused by a version
  mismatch between **PyQt6** (bindings) and **PyQt6-Qt6** (Qt DLLs).
- **Pinned a matched set:** `PyQt6==6.6.1`, `PyQt6-Qt6==6.6.1`,
  `PyQt6-sip==13.6.0`.
- `D-Clinic.spec` now bundles the **complete** PyQt6 runtime via
  `collect_all("PyQt6")` (all Qt DLLs + the `platforms\qwindows.dll` plugin)
  and lists `QtCore/QtGui/QtWidgets/QtPrintSupport/pkgutil` as hidden imports.
- `build.bat` now builds inside a **clean virtual environment** and asserts the
  PyQt6 binding/runtime versions match before packaging.
- Installer `MinVersion` raised to **10.0** (Windows 10/11 only).
- The only OS-specific call (`winreg` for the Machine ID) is available on
  Windows 10/11; no Windows-version-specific APIs are used.

### 2. Dark Mode (Night Mode)
- New **Light / Dark** selector in **Settings**, saved permanently and applied
  **immediately** (no restart).
- Covers the whole UI — sidebar, header, cards, tables, forms, dialogs, tabs,
  login/activation, About page and the hand-painted **charts**.
- **RTL for Dari/Persian preserved** in both themes; brand teal accent kept
  consistent.
- Printed documents stay light on purpose (ink-friendly paper output).

### 3. Professional DEMO / FULL license system (offline, Ed25519)
- **FULL** — perpetual, no patient limit, no watermark.
- **DEMO** — expiry (7/15/30/custom days), configurable patient cap, and a
  `DEMO VERSION - ZENITH SOFT` watermark on every printed/PDF page.
- **About page** shows license type, remaining days, expiry and patient quota.
- **Patient cap** enforced when registering new patients on a DEMO license.
- **Security:** signature verified on every startup, machine-locked keys, and
  **Windows clock-rollback detection** (HMAC-protected, machine-bound run-date
  record blocks execution if the clock is moved backwards).
- `tools/keygen.py` extended with `--demo`/`--full`, `--days`/`--expiry`,
  `--max-patients`.
- **Backward compatible** — existing v1.0.0 keys keep working as FULL licenses.

### Database
- Added a `theme` column to `clinics` via an idempotent migration; existing
  databases upgrade automatically with no data loss.

### Remaining risks
- Printed documents remain light in Dark Mode by design (ink-friendly).
- Final sign-off needs a **manual run on a clean Windows 10 and Windows 11**
  machine using the checklist in `docs/WINDOWS_COMPATIBILITY.md`.

---

# D-Clinic v1.0.0 — Release Notes

**Product:** D-Clinic — Dental Clinic Management System
**Vendor:** Zenith Soft
**Version:** 1.0.0 (first commercial release)
**Release date:** 2026-06-14
**Platform:** Windows 10 / 11 — fully offline desktop application

---

## Overview

D-Clinic 1.0.0 is the first commercial release of Zenith Soft's dental clinic management system. It is a fully offline Windows desktop application delivered with a professional installer. The interface is bilingual — Persian/Dari (right-to-left) and English (left-to-right) — and the entire program uses the Jalali (Solar Hijri) calendar. D-Clinic gives a clinic one place to manage patients, clinical work, finances, staff, inventory, and reporting, with professional A4 printing throughout.

---

## Highlights

### Clinical

- **Permanent patient files** with automatic patient codes (P-000001), search by name/phone/code, and personal plus medical information (allergies, medical history, blood type) with a prominent allergy alert banner.
- **Patient file tabs:** Overview & timeline, Dental Chart, Visits/treatments, Treatment Plan, Prescriptions, Payments, Invoices, and Files/attachments.
- **Interactive dental chart (odontogram):** 32 permanent teeth in two anatomical arches using FDI numbering; click a tooth to set its condition (Healthy, Caries, Filling, Root Canal, Crown, Implant, Extracted, Missing) with color coding, a readable legend, and per-tooth treatment history.
- **Treatment Plan module:** plan future treatments per patient (tooth, planned treatment, estimated cost, status, notes) with printable plans.
- **Visits/treatments:** record date, provider, treatment type, tooth, cost, and notes, with optional attachments (X-rays/photos/PDFs) and an optional Next Visit (recall) date.
- **Prescriptions:** editable, saved per patient, with English drug names, dosage, dispense quantity, and instructions; printable.
- **Follow-up & Recall:** a Dashboard panel surfaces patients due for follow-up and patients with unfinished treatment plans.

### Financial

- **Payments & invoices** per patient, with outstanding-balance tracking.
- **Service price list** used across the program.
- **Expenses and profit/loss accounting.**
- **Daily cash report** for end-of-day reconciliation.
- **Dashboard financial insight:** today's and monthly revenue, outstanding balances, and a revenue chart.

### Administration

- **Login with role-based permissions:** Admin, Doctor, and Receptionist.
- **Appointments scheduling.**
- **Staff/doctor registry with payroll** (salary/commission) and printable salary receipts.
- **Inventory/store** for medicines, equipment, and consumables, with stock in/out and low-stock/expiry awareness.
- **Dashboard analytics:** stat cards plus revenue, patient-growth, and common-treatment charts.
- **Settings:** clinic info (name, doctor/owner, phone, city, address, email, logo), UI language switch (Persian/English), and password change.
- **Professional A4 printing (RTL/LTR)** with clinic logo and details for the patient file, single visit, invoice, prescription, treatment plan, salary receipt, and daily cash report.

### Platform / Build

- **Windows 10/11 desktop application**, fully offline — no internet connection required.
- **Professional installer.** Installed builds store all data and automatic backups in `C:\ProgramData\Zenith Soft\D-Clinic\`.
- **Bilingual UI** (Persian/Dari RTL + English LTR) with a Jalali calendar throughout.
- **Backup & restore:** automatic daily backup, manual backup, export to a chosen location, and restore from file (with a safety copy taken before restore).

### Licensing

- **Per-machine offline activation** secured with Ed25519 signatures. On first run the user sees an Activation screen with a Machine ID; the vendor issues a matching Product Key; activation is verified locally with no internet connection.
- **Customer Registration** after activation captures Clinic Name, Doctor Name, Phone, and City.
- **About page** showing D-Clinic, Zenith Soft, version, license status, the licensed clinic name, and support contact.

---

## Known limitations

- **Single-machine, single-user.** A license activates one computer, and the database is intended for one workstation. LAN multi-user (shared database across reception/doctor workstations) is on the roadmap for a future version.
- **No cloud sync.** Data is local and offline. Optional encrypted cloud backup/sync is planned for a future version.
- **No SMS/WhatsApp reminders yet.** Follow-up and recall are handled by reviewing the Dashboard panel and contacting patients directly. Automated appointment/recall reminders are on the roadmap.
- **Activation is per machine.** Moving to a new computer requires a new Product Key for that machine's Machine ID, plus a restore from backup.

---

*D-Clinic — Zenith Soft. Version 1.0.0. Released 2026-06-14.*
