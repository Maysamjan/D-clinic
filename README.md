# 🦷 D-Clinic — سیستم مدیریت کلینیک دندانپزشکی

A complete **offline desktop** dental clinic management system built for
dental clinics in Afghanistan. Built with **Python + PyQt6 + SQLite**, with
full **Persian/Dari RTL** support, the **Jalali (Solar Hijri) calendar**, a
consistent professional teal theme and the bundled high-quality
**Vazirmatn** font (in `assets/fonts`).

> نرم‌افزار رومیزی مدیریت کلینیک دندانپزشکی — کاملاً آفلاین، با پشتیبانی کامل
> از زبان فارسی/دری و تقویم هجری شمسی.

---

## ✨ Features

| Module | Description |
|---|---|
| 🔐 **Login & Users** | Three roles — Admin, Doctor, Receptionist — with role-based permissions |
| 🩺 **Staff & Payroll** | Register doctors & employees; track salary / commission earned from treatments; record payouts and **print payment receipts** |
| 📦 **Inventory / Store** | Register medicines, equipment and consumables; stock-in / stock-out movements; low-stock and expiry alerts; total store value |
| 👥 **Patients** | One permanent file per patient, auto patient code, fast search by name / phone / code |
| 📋 **Timeline** | Social-media style chronological timeline of every visit & treatment |
| 🦷 **Visits / Treatments** | Date, doctor, treatment type, tooth, notes, cost — admin-extendable treatment types |
| 📎 **Attachments** | Optional X-rays, photos, PDFs and documents per visit (multiple files allowed) |
| 💵 **Finance** | Service cost, partial payments, remaining balance per patient |
| 💲 **Service Pricing** | Editable price list managed by the admin |
| 🧾 **Invoices** | Printable invoices with clinic logo, services and totals (Print + PDF) |
| 📊 **Dashboard & Reports** | Today's patients, revenue, outstanding balances + revenue / growth / treatment charts |
| 🖨 **Printing** | Print complete patient file, single visit, or invoice — professional A4 layouts |
| ⚙ **Clinic Settings** | Clinic name, logo, doctor, phone, address, email — appears on all documents |
| 💾 **Backup** | Automatic daily backup, manual backup, and restore from file |

Everything is stored **locally** in SQLite and works with **no internet
connection**.

---

## 🚀 Getting Started

### Requirements
- Python 3.10+
- Windows (primary target), also runs on Linux / macOS

### Install & Run
```bash
pip install -r requirements.txt
python main.py
```

### Default Login
| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin` |

> پس از اولین ورود، حتماً رمز عبور مدیر را از بخش «کاربران» تغییر دهید.
> (Please change the admin password from the **Users** page after first login.)

---

## 📦 Building a Windows Executable

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name D-Clinic ^
    --add-data "app/resources/styles.qss;app/resources" ^
    --add-data "assets;assets" main.py
```

The resulting `dist/D-Clinic/D-Clinic.exe` is fully portable. Application
data (`data/`, `backups/`, `attachments/`) is created next to the
executable.

---

## 🗂 Project Structure

```
D-clinic/
├── main.py                  # Entry point
├── requirements.txt
├── app/
│   ├── config.py            # Paths & constants
│   ├── database/            # Connection + schema + seed data
│   ├── models/              # Data access (patients, visits, payments, ...)
│   ├── services/            # Jalali calendar, session, backup
│   ├── ui/                  # PyQt6 windows, pages and dialogs
│   │   └── widgets/         # Charts, timeline, stat cards, date edit
│   ├── utils/               # Helpers & print/PDF layouts
│   └── resources/styles.qss # Application theme
└── data / backups / attachments   # Created at runtime (not committed)
```

---

## 🗄 Database Schema

`clinics`, `users`, `staff`, `staff_payments`, `patients`, `treatments`,
`service_prices`, `visits`, `attachments`, `payments`, `invoices`,
`invoice_items`, `inventory_items`, `inventory_movements`, `backups` — all
with proper foreign-key relationships and indexes for fast search.

---

## 🔒 Security Notes
- Passwords are stored as salted **PBKDF2-HMAC-SHA256** hashes.
- Restoring a backup automatically creates a safety copy of the current
  database first.

---

Made for dental clinics across Afghanistan. 🇦🇫
