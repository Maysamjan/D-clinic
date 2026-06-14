"""Visit file-attachment model.

Files are copied into the local ``attachments`` directory, grouped per
patient, so the database only stores relative-friendly paths and the data
stays self-contained for backup.
"""

from __future__ import annotations

import os
import shutil
import time
from typing import Optional

from .. import config
from ..database import db

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
PDF_EXT = {".pdf"}


def _classify(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in PDF_EXT:
        return "pdf"
    return "document"


def add(visit_id: int, patient_id: int, source_path: str) -> Optional[dict]:
    """Copy *source_path* into the attachments store and record it."""
    if not source_path or not os.path.isfile(source_path):
        return None
    config.ensure_dirs()
    patient_dir = os.path.join(config.ATTACHMENTS_DIR, f"patient_{patient_id}")
    os.makedirs(patient_dir, exist_ok=True)

    original = os.path.basename(source_path)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe = f"v{visit_id}_{stamp}_{original}"
    dest = os.path.join(patient_dir, safe)
    # Avoid collisions
    counter = 1
    base, ext = os.path.splitext(dest)
    while os.path.exists(dest):
        dest = f"{base}_{counter}{ext}"
        counter += 1
    shutil.copy2(source_path, dest)

    file_type = _classify(source_path)
    att_id = db.insert(
        """INSERT INTO attachments (visit_id, patient_id, file_path,
           original_name, file_type) VALUES (?, ?, ?, ?, ?)""",
        (visit_id, patient_id, dest, original, file_type),
    )
    return get(att_id)


def get(att_id: int) -> Optional[dict]:
    row = db.query_one("SELECT * FROM attachments WHERE id = ?", (att_id,))
    return dict(row) if row else None


def for_visit(visit_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM attachments WHERE visit_id = ? ORDER BY id", (visit_id,)
    )
    return [dict(r) for r in rows]


def for_patient(patient_id: int) -> list[dict]:
    rows = db.query_all(
        "SELECT * FROM attachments WHERE patient_id = ? ORDER BY id DESC",
        (patient_id,),
    )
    return [dict(r) for r in rows]


def delete(att_id: int) -> None:
    row = get(att_id)
    if row:
        try:
            if os.path.isfile(row["file_path"]):
                os.remove(row["file_path"])
        except OSError:
            pass
    db.execute("DELETE FROM attachments WHERE id = ?", (att_id,))
