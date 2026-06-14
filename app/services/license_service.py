"""Per-machine product-key activation (offline licensing).

How it works
------------
* Every computer has a stable **Machine ID** derived from its hardware.
* The vendor signs that Machine ID with a secret **private key** (using the
  ``tools/keygen.py`` generator) and gives the customer a **Product Key**.
* This application embeds only the matching **public key** and verifies the
  Product Key against the current machine. Because the private key never
  ships with the program, valid keys cannot be forged.
* The activation is stored locally and re-checked against the live hardware
  on every start, so copying the installation (or its data folder) to
  another computer will not work — that machine needs its own key.
"""

from __future__ import annotations

import base64
import hashlib
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
# Product key verification
# ---------------------------------------------------------------------------

def _normalise_key(key: str) -> str:
    return "".join(ch for ch in (key or "").upper()
                   if ch.isalnum())


def format_key(key: str) -> str:
    """Group a product key into 5-char blocks for display."""
    k = _normalise_key(key)
    return "-".join(k[i:i + 5] for i in range(0, len(k), 5))


def verify_product_key(key: str, mid: str | None = None) -> bool:
    """Return True if *key* is a valid product key for this machine."""
    if mid is None:
        mid = machine_id()
    norm = _normalise_key(key)
    # base32 decode (re-pad to a multiple of 8)
    try:
        padded = norm + "=" * ((8 - len(norm) % 8) % 8)
        sig = base64.b32decode(padded)
    except Exception:  # noqa: BLE001
        return False
    if len(sig) != 64:
        return False
    return ed25519.checkvalid(sig, mid.encode("utf-8"), _PUBLIC_KEY)


# ---------------------------------------------------------------------------
# Activation state
# ---------------------------------------------------------------------------

def is_activated() -> bool:
    """True if a stored product key is valid for the *current* machine."""
    if not os.path.isfile(_LICENSE_FILE):
        return False
    try:
        with open(_LICENSE_FILE, "r", encoding="utf-8") as fh:
            stored = fh.read().strip()
    except OSError:
        return False
    return verify_product_key(stored)


def activate(key: str) -> bool:
    """Verify and persist a product key. Returns True on success."""
    if not verify_product_key(key):
        return False
    config.ensure_dirs()
    try:
        with open(_LICENSE_FILE, "w", encoding="utf-8") as fh:
            fh.write(_normalise_key(key))
    except OSError:
        return False
    return True


def deactivate() -> None:
    try:
        if os.path.isfile(_LICENSE_FILE):
            os.remove(_LICENSE_FILE)
    except OSError:
        pass
