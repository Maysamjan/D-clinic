"""Service price-list model."""

from __future__ import annotations

from typing import Optional

from ..database import db


def all_active() -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM service_prices WHERE is_active = 1 ORDER BY name"
    )
    return [dict(r) for r in rows]


def all_services() -> list[dict]:
    rows = db.query_all("SELECT * FROM service_prices ORDER BY name")
    return [dict(r) for r in rows]


def get(service_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM service_prices WHERE id = ?", (service_id,))
    return dict(row) if row else None


def exists(name: str) -> bool:
    row = db.query_one(
        "SELECT id FROM service_prices WHERE name = ?", (name.strip(),)
    )
    return row is not None


def create(name: str, price: float) -> int:
    return db.insert(
        "INSERT INTO service_prices (name, price) VALUES (?, ?)",
        (name.strip(), price),
    )


def update(service_id: int, name: str, price: float, is_active: int = 1) -> None:
    db.execute(
        "UPDATE service_prices SET name = ?, price = ?, is_active = ? WHERE id = ?",
        (name.strip(), price, is_active, service_id),
    )


def delete(service_id: int) -> None:
    db.execute("DELETE FROM service_prices WHERE id = ?", (service_id,))
