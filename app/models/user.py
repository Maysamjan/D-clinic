"""User account model."""

from __future__ import annotations

from typing import Optional

from ..database import db
from ..database.schema import hash_password, verify_password


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the user dict if credentials are valid and account active."""
    row = db.query_one(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (username.strip(),),
    )
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def all_users() -> list[dict]:
    rows = db.query_all("SELECT * FROM users ORDER BY id")
    return [dict(r) for r in rows]


def doctors() -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM users WHERE role IN ('doctor','admin') AND is_active = 1 "
        "ORDER BY full_name"
    )
    return [dict(r) for r in rows]


def get(user_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    return dict(row) if row else None


def username_exists(username: str, exclude_id: Optional[int] = None) -> bool:
    if exclude_id:
        row = db.query_one(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (username.strip(), exclude_id),
        )
    else:
        row = db.query_one(
            "SELECT id FROM users WHERE username = ?", (username.strip(),)
        )
    return row is not None


def create(username: str, password: str, full_name: str, role: str) -> int:
    return db.insert(
        "INSERT INTO users (username, password_hash, full_name, role) "
        "VALUES (?, ?, ?, ?)",
        (username.strip(), hash_password(password), full_name, role),
    )


def update(user_id: int, full_name: str, role: str,
           is_active: int, password: Optional[str] = None) -> None:
    if password:
        db.execute(
            "UPDATE users SET full_name = ?, role = ?, is_active = ?, "
            "password_hash = ? WHERE id = ?",
            (full_name, role, is_active, hash_password(password), user_id),
        )
    else:
        db.execute(
            "UPDATE users SET full_name = ?, role = ?, is_active = ? WHERE id = ?",
            (full_name, role, is_active, user_id),
        )


def delete(user_id: int) -> None:
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))


def count() -> int:
    row = db.query_one("SELECT COUNT(*) AS c FROM users")
    return row["c"] if row else 0
