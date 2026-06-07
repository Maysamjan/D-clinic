"""Database backup and restore service.

Supports manual backups, an automatic daily backup that runs at most once
per day on startup, and restoring from a chosen backup file. Backups use
SQLite's online backup API so they are consistent even while the database
is open.
"""

from __future__ import annotations

import datetime
import os
import shutil
import sqlite3

from .. import config
from ..database import db


def _record_backup(path: str, kind: str) -> None:
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    db.execute(
        "INSERT INTO backups (file_path, kind, size_bytes) VALUES (?, ?, ?)",
        (path, kind, size),
    )


def create_backup(kind: str = "manual", dest_path: str | None = None) -> str:
    """Create a consistent backup copy of the database.

    Returns the path to the created backup file.
    """
    config.ensure_dirs()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if dest_path is None:
        dest_path = os.path.join(config.BACKUP_DIR, f"backup_{kind}_{stamp}.db")

    source = db.get_connection()
    dest = sqlite3.connect(dest_path)
    try:
        source.commit()
        source.backup(dest)
    finally:
        dest.close()

    _record_backup(dest_path, kind)
    if kind == "auto":
        _rotate_auto_backups()
    return dest_path


def _rotate_auto_backups() -> None:
    """Keep only the most recent automatic backups on disk."""
    autos = sorted(
        (f for f in os.listdir(config.BACKUP_DIR)
         if f.startswith("backup_auto_") and f.endswith(".db")),
        reverse=True,
    )
    for stale in autos[config.MAX_AUTO_BACKUPS:]:
        try:
            os.remove(os.path.join(config.BACKUP_DIR, stale))
        except OSError:
            pass


def auto_backup_if_needed() -> str | None:
    """Run a daily automatic backup if one hasn't been made today."""
    today = datetime.date.today().isoformat()
    row = db.query_one(
        "SELECT created_at FROM backups WHERE kind = 'auto' "
        "ORDER BY id DESC LIMIT 1"
    )
    if row and str(row["created_at"]).startswith(today):
        return None
    return create_backup(kind="auto")


def list_backups() -> list[dict]:
    rows = db.query_all("SELECT * FROM backups ORDER BY id DESC")
    result = []
    for r in rows:
        d = dict(r)
        d["exists"] = os.path.isfile(d["file_path"])
        result.append(d)
    return result


def restore_backup(backup_path: str) -> None:
    """Replace the current database with *backup_path*.

    A safety copy of the current database is made first. The shared
    connection is closed and reopened so callers must refresh any cached
    data afterwards.
    """
    if not os.path.isfile(backup_path):
        raise FileNotFoundError(backup_path)

    # Validate it is a usable SQLite database before overwriting.
    test = sqlite3.connect(backup_path)
    try:
        test.execute("SELECT name FROM sqlite_master LIMIT 1")
    finally:
        test.close()

    # Safety copy of the existing database.
    if os.path.isfile(config.DB_PATH):
        safety = os.path.join(
            config.BACKUP_DIR,
            "before_restore_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".db",
        )
        shutil.copy2(config.DB_PATH, safety)

    db.close_connection()
    # Remove WAL/SHM side files so the restored db is the single source.
    for ext in ("-wal", "-shm"):
        side = config.DB_PATH + ext
        if os.path.isfile(side):
            try:
                os.remove(side)
            except OSError:
                pass
    shutil.copy2(backup_path, config.DB_PATH)
    db.get_connection()  # reopen
