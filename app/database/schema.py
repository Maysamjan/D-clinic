"""Database schema definition and initialisation.

Creates all tables with proper relationships and seeds the default
admin user, clinic record, treatment types and service prices on first
run.
"""

from __future__ import annotations

import hashlib
import os

from .. import config
from . import db

SCHEMA = """
-- Clinic configuration (single row, id = 1) ------------------------------
CREATE TABLE IF NOT EXISTS clinics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL DEFAULT '',
    owner_name    TEXT DEFAULT '',
    phone         TEXT DEFAULT '',
    address       TEXT DEFAULT '',
    email         TEXT DEFAULT '',
    logo_path     TEXT DEFAULT '',
    created_at    TEXT DEFAULT (datetime('now'))
);

-- Application users -------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL DEFAULT 'receptionist',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- Patients ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT UNIQUE,            -- human friendly patient id e.g. P-000123
    full_name     TEXT NOT NULL,
    phone         TEXT DEFAULT '',
    gender        TEXT DEFAULT '',
    age           INTEGER,
    address       TEXT DEFAULT '',
    notes         TEXT DEFAULT '',
    registered_at TEXT DEFAULT (date('now')),
    created_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_name  ON patients(full_name);
CREATE INDEX IF NOT EXISTS idx_patients_code  ON patients(code);

-- Treatment types (catalog) ----------------------------------------------
CREATE TABLE IF NOT EXISTS treatments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    default_price REAL NOT NULL DEFAULT 0,
    is_active     INTEGER NOT NULL DEFAULT 1
);

-- Service prices (price list shown in settings) --------------------------
CREATE TABLE IF NOT EXISTS service_prices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    price         REAL NOT NULL DEFAULT 0,
    is_active     INTEGER NOT NULL DEFAULT 1
);

-- Visits / treatments performed ------------------------------------------
CREATE TABLE IF NOT EXISTS visits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL,
    doctor_id     INTEGER,
    doctor_name   TEXT DEFAULT '',
    treatment_id  INTEGER,
    treatment_name TEXT DEFAULT '',
    tooth         TEXT DEFAULT '',
    visit_date    TEXT NOT NULL DEFAULT (date('now')),
    notes         TEXT DEFAULT '',
    cost          REAL NOT NULL DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id)  REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (treatment_id) REFERENCES treatments(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_date);

-- File attachments for visits --------------------------------------------
CREATE TABLE IF NOT EXISTS attachments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id      INTEGER NOT NULL,
    patient_id    INTEGER NOT NULL,
    file_path     TEXT NOT NULL,
    original_name TEXT DEFAULT '',
    file_type     TEXT DEFAULT '',
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_attachments_visit ON attachments(visit_id);

-- Payments ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL,
    visit_id      INTEGER,
    amount        REAL NOT NULL DEFAULT 0,
    method        TEXT DEFAULT 'cash',
    pay_date      TEXT NOT NULL DEFAULT (date('now')),
    notes         TEXT DEFAULT '',
    created_by    INTEGER,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_payments_patient ON payments(patient_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(pay_date);

-- Invoices ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    number        TEXT UNIQUE,
    patient_id    INTEGER NOT NULL,
    total         REAL NOT NULL DEFAULT 0,
    paid          REAL NOT NULL DEFAULT 0,
    issue_date    TEXT NOT NULL DEFAULT (date('now')),
    notes         TEXT DEFAULT '',
    created_by    INTEGER,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id    INTEGER NOT NULL,
    description   TEXT NOT NULL,
    amount        REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- Clinic staff / doctors registry (for payroll) -------------------------
CREATE TABLE IF NOT EXISTS staff (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT UNIQUE,               -- staff id e.g. E-000001
    full_name     TEXT NOT NULL,
    position      TEXT DEFAULT '',          -- داکتر / نرس / پذیرش / خدمات ...
    phone         TEXT DEFAULT '',
    pay_type      TEXT DEFAULT 'salary',    -- salary | commission | both
    base_salary   REAL NOT NULL DEFAULT 0,  -- monthly salary
    commission_pct REAL NOT NULL DEFAULT 0, -- percent of treatments performed
    is_provider   INTEGER NOT NULL DEFAULT 0, -- shows in visit "doctor" list
    is_active     INTEGER NOT NULL DEFAULT 1,
    notes         TEXT DEFAULT '',
    created_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_staff_active ON staff(is_active);

-- Payments made TO staff (salary / commission payouts) -------------------
CREATE TABLE IF NOT EXISTS staff_payments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id      INTEGER NOT NULL,
    amount        REAL NOT NULL DEFAULT 0,
    kind          TEXT DEFAULT 'salary',    -- salary | commission | bonus
    period        TEXT DEFAULT '',          -- e.g. حمل ۱۴۰۵
    method        TEXT DEFAULT 'cash',
    pay_date      TEXT NOT NULL DEFAULT (date('now')),
    notes         TEXT DEFAULT '',
    receipt_no    TEXT,
    created_by    INTEGER,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_staffpay_staff ON staff_payments(staff_id);

-- Inventory / store room (medicines, equipment, consumables) -------------
CREATE TABLE IF NOT EXISTS inventory_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    category      TEXT DEFAULT 'medicine',   -- medicine | equipment | consumable
    unit          TEXT DEFAULT 'عدد',        -- عدد / بسته / میلی‌لیتر ...
    quantity      REAL NOT NULL DEFAULT 0,
    min_quantity  REAL NOT NULL DEFAULT 0,   -- reorder level
    unit_price    REAL NOT NULL DEFAULT 0,
    supplier      TEXT DEFAULT '',
    expiry_date   TEXT,                       -- ISO date (medicines), nullable
    notes         TEXT DEFAULT '',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_inv_name ON inventory_items(name);
CREATE INDEX IF NOT EXISTS idx_inv_cat ON inventory_items(category);

-- Stock movements (in / out) ---------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_movements (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id       INTEGER NOT NULL,
    change        REAL NOT NULL DEFAULT 0,    -- positive = in, negative = out
    reason        TEXT DEFAULT 'purchase',    -- purchase | use | adjust | expire
    note          TEXT DEFAULT '',
    movement_date TEXT NOT NULL DEFAULT (date('now')),
    created_by    INTEGER,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_invmov_item ON inventory_movements(item_id);

-- Appointments / scheduling --------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER,
    patient_name  TEXT DEFAULT '',           -- for walk-ins / new prospects
    phone         TEXT DEFAULT '',
    staff_id      INTEGER,
    doctor_name   TEXT DEFAULT '',
    appt_date     TEXT NOT NULL DEFAULT (date('now')),
    appt_time     TEXT DEFAULT '',            -- HH:MM
    reason        TEXT DEFAULT '',
    status        TEXT DEFAULT 'scheduled',   -- scheduled | done | cancelled | noshow
    notes         TEXT DEFAULT '',
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_appt_date ON appointments(appt_date);

-- Dental chart (one row per tooth per patient) ---------------------------
CREATE TABLE IF NOT EXISTS tooth_chart (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL,
    tooth         TEXT NOT NULL,              -- FDI number, e.g. 26
    condition     TEXT DEFAULT 'healthy',
    note          TEXT DEFAULT '',
    updated_at    TEXT DEFAULT (datetime('now')),
    UNIQUE (patient_id, tooth),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Prescriptions ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS prescriptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id    INTEGER NOT NULL,
    doctor_name   TEXT DEFAULT '',
    presc_date    TEXT NOT NULL DEFAULT (date('now')),
    notes         TEXT DEFAULT '',
    created_by    INTEGER,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS prescription_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    drug            TEXT NOT NULL,
    dosage          TEXT DEFAULT '',
    quantity        TEXT DEFAULT '',          -- total to dispense, e.g. ۲۰ عدد / ۲ تخته
    instructions    TEXT DEFAULT '',
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
);

-- Clinic expenses --------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT DEFAULT 'other',
    description   TEXT DEFAULT '',
    amount        REAL NOT NULL DEFAULT 0,
    expense_date  TEXT NOT NULL DEFAULT (date('now')),
    paid_to       TEXT DEFAULT '',
    created_by    INTEGER,
    created_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_expense_date ON expenses(expense_date);

-- Backup history ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS backups (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path     TEXT NOT NULL,
    kind          TEXT DEFAULT 'manual',   -- manual | auto
    size_bytes    INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);
"""

DEFAULT_TREATMENTS = [
    ("معاینه", 200),
    ("ترمیم (پر کردن)", 800),
    ("کشیدن دندان", 500),
    ("عصب‌کشی", 2500),
    ("جرم‌گیری", 600),
    ("ایمپلنت", 25000),
    ("ارتودنسی", 40000),
    ("جراحی", 3000),
    ("بلیچینگ (سفید کردن)", 3500),
    ("روکش (کراون)", 4000),
]

DEFAULT_SERVICES = [
    ("معاینه", 200),
    ("ترمیم (پر کردن)", 800),
    ("کشیدن دندان", 500),
    ("عصب‌کشی", 2500),
    ("جرم‌گیری", 600),
    ("ایمپلنت", 25000),
    ("روکش (کراون)", 4000),
]


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a per-hash salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return "pbkdf2$" + salt.hex() + "$" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    """Verify a plain password against a stored hash."""
    try:
        algo, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2":
            return False
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return dk.hex() == hash_hex
    except (ValueError, AttributeError):
        return False


def init_db() -> None:
    """Create tables and seed default data if the database is new."""
    config.ensure_dirs()
    conn = db.get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    _migrate()
    _seed_defaults()


def _migrate() -> None:
    """Apply lightweight, idempotent schema migrations to older databases."""
    cols = {r["name"] for r in db.query_all("PRAGMA table_info(visits)")}
    if "staff_id" not in cols:
        db.execute("ALTER TABLE visits ADD COLUMN staff_id INTEGER")

    staff_cols = {r["name"] for r in db.query_all("PRAGMA table_info(staff)")}
    if "code" not in staff_cols:
        db.execute("ALTER TABLE staff ADD COLUMN code TEXT")
    # Backfill short staff codes for any rows missing one.
    for row in db.query_all("SELECT id FROM staff WHERE code IS NULL OR code = ''"):
        db.execute("UPDATE staff SET code = ? WHERE id = ?",
                   (str(row["id"]), row["id"]))

    # Patient medical/safety fields.
    pcols = {r["name"] for r in db.query_all("PRAGMA table_info(patients)")}
    for col in ("allergies", "medical_history", "blood_type"):
        if col not in pcols:
            db.execute(f"ALTER TABLE patients ADD COLUMN {col} TEXT DEFAULT ''")

    # Clinic UI language.
    ccols = {r["name"] for r in db.query_all("PRAGMA table_info(clinics)")}
    if "language" not in ccols:
        db.execute("ALTER TABLE clinics ADD COLUMN language TEXT DEFAULT 'fa'")

    # Prescription dispense quantity.
    if db.query_one("SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='prescription_items'"):
        icols = {r["name"] for r in
                 db.query_all("PRAGMA table_info(prescription_items)")}
        if "quantity" not in icols:
            db.execute("ALTER TABLE prescription_items "
                       "ADD COLUMN quantity TEXT DEFAULT ''")


def _seed_defaults() -> None:
    # Default clinic row
    if db.query_one("SELECT id FROM clinics WHERE id = 1") is None:
        db.execute(
            "INSERT INTO clinics (id, name, owner_name) VALUES (1, ?, ?)",
            ("کلینیک دندانپزشکی", ""),
        )

    # Default admin user
    if db.query_one("SELECT id FROM users LIMIT 1") is None:
        db.execute(
            "INSERT INTO users (username, password_hash, full_name, role) "
            "VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin"), "مدیر سیستم", config.ROLE_ADMIN),
        )

    # Default treatment catalog
    if db.query_one("SELECT id FROM treatments LIMIT 1") is None:
        db.executemany(
            "INSERT INTO treatments (name, default_price) VALUES (?, ?)",
            DEFAULT_TREATMENTS,
        )

    # Default service price list
    if db.query_one("SELECT id FROM service_prices LIMIT 1") is None:
        db.executemany(
            "INSERT INTO service_prices (name, price) VALUES (?, ?)",
            DEFAULT_SERVICES,
        )
