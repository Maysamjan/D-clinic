"""Clinic settings model (single row table)."""

from __future__ import annotations

from ..database import db


def get() -> dict:
    """Return the clinic settings as a dict (always row id 1)."""
    row = db.query_one("SELECT * FROM clinics WHERE id = 1")
    if row is None:
        db.execute("INSERT INTO clinics (id, name) VALUES (1, '')")
        row = db.query_one("SELECT * FROM clinics WHERE id = 1")
    return dict(row)


def update(name: str, owner_name: str, phone: str, address: str,
           email: str, logo_path: str) -> None:
    db.execute(
        """UPDATE clinics SET name = ?, owner_name = ?, phone = ?,
           address = ?, email = ?, logo_path = ? WHERE id = 1""",
        (name, owner_name, phone, address, email, logo_path),
    )


def get_language() -> str:
    row = db.query_one("SELECT language FROM clinics WHERE id = 1")
    return (row["language"] if row and row["language"] else "fa")


def set_language(lang: str) -> None:
    db.execute("UPDATE clinics SET language = ? WHERE id = 1", (lang,))
