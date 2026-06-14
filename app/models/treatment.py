"""Treatment-type catalog model."""

from __future__ import annotations

from typing import Optional

from ..database import db


def all_active() -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM treatments WHERE is_active = 1 ORDER BY name"
    )
    return [dict(r) for r in rows]


def all_treatments() -> list[dict]:
    rows = db.query_all("SELECT * FROM treatments ORDER BY name")
    return [dict(r) for r in rows]


def get(treatment_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM treatments WHERE id = ?", (treatment_id,))
    return dict(row) if row else None


def exists(name: str) -> bool:
    row = db.query_one("SELECT id FROM treatments WHERE name = ?", (name.strip(),))
    return row is not None


def create(name: str, default_price: float) -> int:
    return db.insert(
        "INSERT INTO treatments (name, default_price) VALUES (?, ?)",
        (name.strip(), default_price),
    )


def update(treatment_id: int, name: str, default_price: float,
           is_active: int = 1) -> None:
    db.execute(
        "UPDATE treatments SET name = ?, default_price = ?, is_active = ? "
        "WHERE id = ?",
        (name.strip(), default_price, is_active, treatment_id),
    )


def delete(treatment_id: int) -> None:
    db.execute("DELETE FROM treatments WHERE id = ?", (treatment_id,))
