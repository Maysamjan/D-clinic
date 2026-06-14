"""SQLite connection manager.

A single shared connection is used because the application is a
single-user desktop program. Rows are returned as ``sqlite3.Row`` so they
can be accessed both by index and by column name.
"""

from __future__ import annotations

import sqlite3
import threading
from typing import Any, Iterable, Optional

from .. import config

_connection: Optional[sqlite3.Connection] = None
_lock = threading.RLock()


def get_connection() -> sqlite3.Connection:
    """Return the shared SQLite connection, opening it if needed."""
    global _connection
    with _lock:
        if _connection is None:
            config.ensure_dirs()
            _connection = sqlite3.connect(config.DB_PATH, check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute("PRAGMA foreign_keys = ON")
            _connection.execute("PRAGMA journal_mode = WAL")
        return _connection


def close_connection() -> None:
    """Close the shared connection (used before restoring a backup)."""
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None


def execute(query: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
    """Execute a write query and commit."""
    with _lock:
        conn = get_connection()
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return cur


def executemany(query: str, seq_of_params: Iterable[Iterable[Any]]) -> None:
    with _lock:
        conn = get_connection()
        conn.executemany(query, [tuple(p) for p in seq_of_params])
        conn.commit()


def query_all(query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    """Run a SELECT and return all rows."""
    with _lock:
        conn = get_connection()
        cur = conn.execute(query, tuple(params))
        return cur.fetchall()


def query_one(query: str, params: Iterable[Any] = ()) -> Optional[sqlite3.Row]:
    """Run a SELECT and return the first row (or ``None``)."""
    with _lock:
        conn = get_connection()
        cur = conn.execute(query, tuple(params))
        return cur.fetchone()


def insert(query: str, params: Iterable[Any] = ()) -> int:
    """Run an INSERT and return the new row id."""
    with _lock:
        conn = get_connection()
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return int(cur.lastrowid)
