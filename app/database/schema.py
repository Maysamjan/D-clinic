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
    _seed_defaults()


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
