"""Per-machine product-key activation and DEMO/FULL licensing (fully offline).

How it works
------------
* Every computer has a stable **Machine ID** derived from its hardware.
* The vendor signs a small **license payload** (license type, expiry date,
  patient limit and the target Machine ID) with a secret **private key**
  using ``tools/keygen.py`` and gives the customer a **Product Key**.
* This application embeds only the matching **public key** and verifies the
  Product Key against the current machine. Because the private key never
  ships with the program, valid keys cannot be forged.
* The activation is stored locally and re-checked against the live hardware
  on **every start**, so copying the installation (or its data folder) to
  another computer will not work — that machine needs its own key.

License types
-------------
* ``FULL`` — perpetual, no expiry, no patient limit, no watermark.
* ``DEMO`` — expires on a date, caps the number of patients and stamps a
  ``DEMO VERSION - ZENITH SOFT`` watermark on every printed document.

Two key formats are supported:

* **v2 signed token** (``DCL2.<payload>.<signature>``) — carries the license
  type, issue/expiry dates and patient limit. Produced by the current
  ``keygen.py``.
* **legacy bare-signature key** — a base32 Ed25519 signature of the Machine
  ID, as shipped in v1.0.0. These keep working and are treated as a
  perpetual **FULL** license so existing customers are never locked out.

Anti-tamper clock protection
----------------------------
The last successful run date (and the furthest date ever seen) is stored in
a machine-bound, HMAC-protected ``runstate`` file. If the system clock is
moved backwards past a small tolerance to dodge a DEMO expiry, the rollback
is detected on the next start and execution is blocked.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import os
import platform
import uuid

from .. import config
from . import ed25519

# Public verification key (hex). The matching private key is held only by the
# vendor and is never distributed with the application.
PUBLIC_KEY_HEX = "43c889351bdc0f4cf56c09c22e08433ff99d755fc198294c572035ddef81a661"
_PUBLIC_KEY = bytes.fromhex(PUBLIC_KEY_HEX)

_LICENSE_FILE = os.path.join(config.DATA_DIR, "license.dat")
_RUNSTATE_FILE = os.path.join(config.DATA_DIR, "runstate.dat")

# License types.
TYPE_FULL = "FULL"
TYPE_DEMO = "DEMO"

# v2 token marker.
_V2_PREFIX = "DCL2."

# How many days the clock may legitimately drift backwards (e.g. a user
# correcting a wrong date) before we treat it as a rollback attempt.
_ROLLBACK_TOLERANCE_DAYS = 2

# The fixed watermark text stamped on DEMO documents.
WATERMARK_TEXT = "DEMO VERSION - ZENITH SOFT"


# ---------------------------------------------------------------------------
# Machine fingerprint
# ---------------------------------------------------------------------------

def _raw_fingerprint() -> str:
    """A stable, hardware-derived string for this computer."""
    parts: list[str] = []

    # Windows: the Cryptography MachineGuid is very stable across reboots.
    if platform.system() == "Windows":
        try:
            import winreg  # type: ignore

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            parts.append(str(guid))
        except Exception:  # noqa: BLE001
            pass

    # Cross-platform hardware-ish identifiers.
    parts.append(format(uuid.getnode(), "x"))          # MAC address
    parts.append(platform.node())                       # hostname
    parts.append(platform.machine())                    # cpu arch
    return "|".join(p for p in parts if p)


def machine_id() -> str:
    """Return the canonical Machine ID (20 uppercase hex chars)."""
    digest = hashlib.sha256(_raw_fingerprint().encode("utf-8")).hexdigest()
    return digest[:20].upper()


def machine_id_display() -> str:
    """Machine ID grouped for readability, e.g. ``A1B2C-D3E4F-...``."""
    mid = machine_id()
    return "-".join(mid[i:i + 5] for i in range(0, len(mid), 5))


# ---------------------------------------------------------------------------
# Low-level encoding helpers
# ---------------------------------------------------------------------------

def _normalise_key(key: str) -> str:
    return "".join(ch for ch in (key or "").upper() if ch.isalnum())


def format_key(key: str) -> str:
    """Group a legacy product key into 5-char blocks for display."""
    k = _normalise_key(key)
    return "-".join(k[i:i + 5] for i in range(0, len(k), 5))


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * ((4 - len(text) % 4) % 4)
    return base64.urlsafe_b64decode(text + pad)


# ---------------------------------------------------------------------------
# License payload (v2 signed token)
# ---------------------------------------------------------------------------
#
# Payload is a compact, signed, pipe-delimited ASCII string:
#
#     DCLIC1|<type>|<machine_id>|<issue>|<expiry>|<max_patients>
#
#   type          FULL | DEMO
#   machine_id    normalised 20-hex Machine ID this key is locked to
#   issue         YYYYMMDD  (issue date)
#   expiry        YYYYMMDD  ("" = never, used by FULL)
#   max_patients  integer   (0 = unlimited, used by FULL)

_PAYLOAD_TAG = "DCLIC1"


def build_payload(license_type: str, mid: str, issue: str, expiry: str,
                  max_patients: int) -> str:
    """Build the canonical payload string that gets signed (vendor side)."""
    return "|".join([
        _PAYLOAD_TAG, license_type, _normalise_key(mid),
        issue or "", expiry or "", str(int(max_patients or 0)),
    ])


def make_token(payload: str, signature: bytes) -> str:
    """Assemble a v2 product key from a signed payload (vendor side)."""
    return (_V2_PREFIX + _b64url_encode(payload.encode("utf-8"))
            + "." + _b64url_encode(signature))


def _parse_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.date(int(value[:4]), int(value[4:6]), int(value[6:8]))
    except (ValueError, IndexError):
        return None


def _parse_v2(text: str, mid: str) -> dict | None:
    """Verify and decode a v2 signed token. Returns the license dict or None."""
    body = "".join(text.split())[len(_V2_PREFIX):]
    parts = body.split(".")
    if len(parts) != 2:
        return None
    try:
        payload_bytes = _b64url_decode(parts[0])
        signature = _b64url_decode(parts[1])
    except Exception:  # noqa: BLE001
        return None
    if len(signature) != 64:
        return None
    if not ed25519.checkvalid(signature, payload_bytes, _PUBLIC_KEY):
        return None
    try:
        payload = payload_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None
    fields = payload.split("|")
    if len(fields) != 6 or fields[0] != _PAYLOAD_TAG:
        return None
    _tag, ltype, key_mid, issue, expiry, max_pat = fields
    if ltype not in (TYPE_FULL, TYPE_DEMO):
        return None
    # The token must be bound to *this* machine.
    if _normalise_key(key_mid) != _normalise_key(mid):
        return None
    try:
        limit = int(max_pat or 0)
    except ValueError:
        limit = 0
    return {
        "format": "v2",
        "type": ltype,
        "machine_id": _normalise_key(key_mid),
        "issue_date": _parse_date(issue),
        "expiry_date": _parse_date(expiry),
        "max_patients": limit,
        "raw": text.strip(),
    }


def _parse_legacy(text: str, mid: str) -> dict | None:
    """Verify a legacy bare-signature key (treated as perpetual FULL)."""
    norm = _normalise_key(text)
    try:
        padded = norm + "=" * ((8 - len(norm) % 8) % 8)
        sig = base64.b32decode(padded)
    except Exception:  # noqa: BLE001
        return None
    if len(sig) != 64:
        return None
    if not ed25519.checkvalid(sig, mid.encode("utf-8"), _PUBLIC_KEY):
        return None
    return {
        "format": "legacy",
        "type": TYPE_FULL,
        "machine_id": _normalise_key(mid),
        "issue_date": None,
        "expiry_date": None,
        "max_patients": 0,
        "raw": text.strip(),
    }


def parse_license(text: str, mid: str | None = None) -> dict | None:
    """Verify *text* against this machine and return the license dict, or None.

    Accepts both the v2 signed token and the legacy bare-signature key.
    Only the cryptographic signature and machine binding are checked here —
    expiry/rollback are evaluated separately by :func:`status`.
    """
    if not text:
        return None
    if mid is None:
        mid = machine_id()
    text = text.strip()
    if text.startswith(_V2_PREFIX):
        return _parse_v2(text, mid)
    return _parse_legacy(text, mid)


def verify_product_key(key: str, mid: str | None = None) -> bool:
    """Backward-compatible boolean check that *key* is valid for this machine."""
    return parse_license(key, mid) is not None


# ---------------------------------------------------------------------------
# Stored activation
# ---------------------------------------------------------------------------

def _read_stored() -> str | None:
    if not os.path.isfile(_LICENSE_FILE):
        return None
    try:
        with open(_LICENSE_FILE, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return None


def stored_license() -> dict | None:
    """Return the parsed, signature-valid license stored on this machine."""
    stored = _read_stored()
    if not stored:
        return None
    return parse_license(stored)


def is_activated() -> bool:
    """True if a stored product key's signature is valid for this machine.

    Note: this only checks the cryptographic signature + machine binding (so
    the activation screen is not shown again for an expired DEMO). Whether the
    app may actually run is decided by :func:`status`.
    """
    return stored_license() is not None


def activate(key: str) -> bool:
    """Verify and persist a product key. Returns True on success."""
    if parse_license(key) is None:
        return False
    config.ensure_dirs()
    try:
        with open(_LICENSE_FILE, "w", encoding="utf-8") as fh:
            fh.write(key.strip())
    except OSError:
        return False
    # Seed/refresh the secure run-date record so a fresh activation starts clean.
    _write_runstate(datetime.date.today())
    return True


def deactivate() -> None:
    try:
        if os.path.isfile(_LICENSE_FILE):
            os.remove(_LICENSE_FILE)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Secure run-date record (clock-rollback protection)
# ---------------------------------------------------------------------------

def _runstate_key() -> bytes:
    """A machine-bound HMAC key so the runstate file cannot be hand-edited."""
    return hashlib.sha256(
        b"ZENITH-SOFT-RUNSTATE|" + machine_id().encode("utf-8")).digest()


def _write_runstate(today: datetime.date, max_seen: datetime.date | None = None) -> None:
    if max_seen is None or today > max_seen:
        max_seen = today
    config.ensure_dirs()
    payload = {"last": today.isoformat(), "max": max_seen.isoformat()}
    msg = (payload["last"] + "|" + payload["max"]).encode("utf-8")
    payload["mac"] = hmac.new(_runstate_key(), msg, hashlib.sha256).hexdigest()
    try:
        with open(_RUNSTATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
    except OSError:
        pass


def _read_runstate() -> dict | None:
    if not os.path.isfile(_RUNSTATE_FILE):
        return None
    try:
        with open(_RUNSTATE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        last = data.get("last", "")
        mx = data.get("max", "")
        mac = data.get("mac", "")
        expected = hmac.new(
            _runstate_key(), (last + "|" + mx).encode("utf-8"),
            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, mac):
            return None  # tampered / not ours
        return {
            "last": datetime.date.fromisoformat(last),
            "max": datetime.date.fromisoformat(mx),
        }
    except (OSError, ValueError, KeyError):
        return None


def record_run_and_check_clock() -> tuple[bool, str]:
    """Update the secure run record and detect a backwards clock change.

    Returns ``(ok, reason)``. When ``ok`` is False the system clock appears to
    have been moved backwards (a likely attempt to dodge a DEMO expiry) and the
    caller should block execution.
    """
    today = datetime.date.today()
    state = _read_runstate()
    if state is None:
        # No trustworthy history yet — start one. (Missing or corrupted file is
        # not, by itself, treated as a rollback so legitimate users are never
        # bricked by a deleted data folder.)
        _write_runstate(today)
        return True, ""
    max_seen = state["max"]
    if today < max_seen - datetime.timedelta(days=_ROLLBACK_TOLERANCE_DAYS):
        # Clock moved meaningfully into the past. Do NOT advance the record.
        return False, "clock_rollback"
    _write_runstate(today, max_seen)
    return True, ""


# ---------------------------------------------------------------------------
# Runtime license status
# ---------------------------------------------------------------------------

def status() -> dict:
    """Full license status used to gate startup and drive the About page.

    Keys:
        activated      bool — a signature-valid license is stored
        ok             bool — the app may run right now
        reason         str  — '' | 'not_activated' | 'expired' | 'clock_rollback'
        type           'FULL' | 'DEMO' | ''
        is_demo        bool
        expiry_date    datetime.date | None
        days_remaining int | None  (DEMO only)
        max_patients   int  (0 = unlimited)
        patient_count  int
    """
    info = {
        "activated": False, "ok": False, "reason": "not_activated",
        "type": "", "is_demo": False, "expiry_date": None,
        "days_remaining": None, "max_patients": 0, "patient_count": 0,
    }
    lic = stored_license()
    if lic is None:
        return info
    info["activated"] = True
    info["type"] = lic["type"]
    info["is_demo"] = lic["type"] == TYPE_DEMO
    info["expiry_date"] = lic["expiry_date"]
    info["max_patients"] = lic["max_patients"]

    # Patient usage (best-effort; the DB may not be ready in odd states).
    try:
        from ..models import patient as patient_model
        info["patient_count"] = patient_model.count()
    except Exception:  # noqa: BLE001
        info["patient_count"] = 0

    # Clock-rollback protection always applies.
    ok_clock, clock_reason = record_run_and_check_clock()
    if not ok_clock:
        info["reason"] = clock_reason
        return info

    today = datetime.date.today()
    if lic["expiry_date"] is not None:
        remaining = (lic["expiry_date"] - today).days
        info["days_remaining"] = remaining
        if remaining < 0:
            info["reason"] = "expired"
            return info

    info["ok"] = True
    info["reason"] = ""
    return info


def is_demo() -> bool:
    """True when the active license is a DEMO license (drives the watermark)."""
    lic = stored_license()
    return bool(lic and lic["type"] == TYPE_DEMO)


def can_add_patient() -> tuple[bool, str]:
    """Enforce the DEMO patient cap. Returns ``(allowed, reason_key)``."""
    lic = stored_license()
    if lic is None or lic["type"] != TYPE_DEMO:
        return True, ""
    limit = lic["max_patients"] or 0
    if limit <= 0:
        return True, ""
    try:
        from ..models import patient as patient_model
        count = patient_model.count()
    except Exception:  # noqa: BLE001
        return True, ""
    if count >= limit:
        return False, "patient_limit"
    return True, ""
