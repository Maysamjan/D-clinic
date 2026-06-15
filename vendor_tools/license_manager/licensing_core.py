"""Standalone licensing core for the Zenith Soft License Manager.

This module is intentionally self-contained (it only depends on the local
``ed25519`` copy) so the License Manager can be built into its own executable
without dragging in the whole D-Clinic application.

CRITICAL: the token format here is byte-for-byte identical to
``app/services/license_service.py`` in D-Clinic v1.1.0, so every key produced
by this tool activates the D-Clinic application. (A compatibility test in
``test_compat.py`` cross-verifies this against the real app module.)
"""

from __future__ import annotations

import base64
import datetime
import os
import sys

import ed25519

# License types — must match license_service.TYPE_*.
TYPE_FULL = "FULL"
TYPE_DEMO = "DEMO"

_V2_PREFIX = "DCL2."
_PAYLOAD_TAG = "DCLIC1"


# ---------------------------------------------------------------------------
# Paths (resolve relative to the executable when frozen, else this file)
# ---------------------------------------------------------------------------

def base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def private_key_path() -> str | None:
    """Locate the vendor private key, searching the usual places.

    Order: next to the tool, the D-Clinic repo root (two levels up), the
    current working directory.
    """
    candidates = [
        os.path.join(base_dir(), "license_private", "private_key.hex"),
        os.path.join(base_dir(), "..", "..", "license_private", "private_key.hex"),
        os.path.join(os.getcwd(), "license_private", "private_key.hex"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def output_dir() -> str:
    path = os.path.join(base_dir(), "generated_licenses")
    os.makedirs(path, exist_ok=True)
    return path


def data_dir() -> str:
    path = os.path.join(base_dir(), "data")
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Machine ID + encoding helpers (identical rules to the app)
# ---------------------------------------------------------------------------

def normalise_machine_id(text: str) -> str:
    return "".join(ch for ch in (text or "").upper() if ch.isalnum())


def machine_id_display(mid: str) -> str:
    m = normalise_machine_id(mid)
    return "-".join(m[i:i + 5] for i in range(0, len(m), 5))


def is_valid_machine_id(text: str) -> bool:
    """A D-Clinic Machine ID is exactly 20 uppercase hex characters."""
    m = normalise_machine_id(text)
    if len(m) != 20:
        return False
    try:
        int(m, 16)
        return True
    except ValueError:
        return False


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


# ---------------------------------------------------------------------------
# Token building / signing
# ---------------------------------------------------------------------------

def build_payload(license_type: str, mid: str, issue: str, expiry: str,
                  max_patients: int) -> str:
    return "|".join([
        _PAYLOAD_TAG, license_type, normalise_machine_id(mid),
        issue or "", expiry or "", str(int(max_patients or 0)),
    ])


def make_token(payload: str, signature: bytes) -> str:
    return (_V2_PREFIX + _b64url_encode(payload.encode("utf-8"))
            + "." + _b64url_encode(signature))


class LicensingError(Exception):
    pass


def _load_private() -> bytes:
    path = private_key_path()
    if not path:
        raise LicensingError(
            "Private key not found. Place it at license_private/private_key.hex "
            "next to the License Manager.")
    with open(path, "r", encoding="utf-8") as fh:
        return bytes.fromhex(fh.read().strip())


def public_key_hex() -> str:
    """Public half of the loaded private key (for a one-time sanity display)."""
    return ed25519.publickey(_load_private()).hex()


def generate_license(license_type: str, machine_id: str,
                     days: int | None = None,
                     expiry: datetime.date | None = None,
                     max_patients: int = 0) -> dict:
    """Sign and return a DCL2 product key plus its metadata.

    Returns a dict with: product_key, license_type, machine_id (normalised),
    issue_date, expiry_date (date|None), max_patients.
    """
    if not is_valid_machine_id(machine_id):
        raise LicensingError(
            "Invalid Machine ID — it must be 20 hex characters "
            "(e.g. CB103-6007C-2FA0C-6EF63).")

    sk = _load_private()
    pk = ed25519.publickey(sk)
    mid = normalise_machine_id(machine_id)
    today = datetime.date.today()

    if license_type == TYPE_DEMO:
        if expiry is None:
            if not days or days <= 0:
                raise LicensingError("A DEMO license needs a positive number of days.")
            expiry = today + datetime.timedelta(days=days)
        cap = int(max_patients or 0)
    else:
        license_type = TYPE_FULL
        expiry = None
        cap = 0

    issue_str = today.strftime("%Y%m%d")
    expiry_str = expiry.strftime("%Y%m%d") if expiry else ""
    payload = build_payload(license_type, mid, issue_str, expiry_str, cap)
    sig = ed25519.signature(payload.encode("utf-8"), sk, pk)
    token = make_token(payload, sig)
    return {
        "product_key": token,
        "license_type": license_type,
        "machine_id": mid,
        "issue_date": today,
        "expiry_date": expiry,
        "max_patients": cap,
    }


def _safe_name(text: str) -> str:
    keep = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in (text or ""))
    return "_".join(keep.split()) or "Clinic"


def license_filename(clinic_name: str, mid: str, license_type: str,
                     days: int | None) -> str:
    """e.g. ClinicName_MACHINEID_DEMO_14days.lic  /  ClinicName_MACHINEID_FULL.lic"""
    mid = normalise_machine_id(mid)
    base = f"{_safe_name(clinic_name)}_{mid}_{license_type}"
    if license_type == TYPE_DEMO and days:
        base += f"_{int(days)}days"
    return base + ".lic"


def write_license_file(result: dict, clinic_name: str, days: int | None) -> str:
    fname = license_filename(clinic_name, result["machine_id"],
                             result["license_type"], days)
    path = os.path.join(output_dir(), fname)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(result["product_key"])
    return path
