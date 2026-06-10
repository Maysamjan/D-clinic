#!/usr/bin/env python3
"""D-Clinic — Vendor Product-Key Generator (KEEP PRIVATE).

⚠️  This tool and the private key file are for the SOFTWARE VENDOR ONLY.
    Never ship them to customers. Anyone holding the private key can
    generate valid product keys.

Usage
-----
A customer installs D-Clinic and reads their **Machine ID** from the
activation screen (e.g. ``A1B2C-D3E4F-5A6B7-C8D9E``). They send it to you.
You run:

    python tools/keygen.py A1B2C-D3E4F-5A6B7-C8D9E

It prints the **Product Key** to give back to the customer, and also writes
a ``<machine-id>.lic`` file they can simply load on the activation screen.

The private key is read from ``license_private/private_key.hex`` (kept out
of the repository). Generate a new key pair with ``--new`` if you ever need
one (then update PUBLIC_KEY_HEX in app/services/license_service.py).
"""

from __future__ import annotations

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import ed25519  # noqa: E402

PRIVATE_KEY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "license_private", "private_key.hex")


def _normalise(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch.isalnum())


def generate_pair() -> None:
    sk = os.urandom(32)
    pk = ed25519.publickey(sk)
    os.makedirs(os.path.dirname(PRIVATE_KEY_PATH), exist_ok=True)
    with open(PRIVATE_KEY_PATH, "w", encoding="utf-8") as fh:
        fh.write(sk.hex())
    print("New key pair generated.")
    print("Private key saved to:", PRIVATE_KEY_PATH, "(KEEP SECRET)")
    print("\nPut this in app/services/license_service.py -> PUBLIC_KEY_HEX:")
    print(pk.hex())


def make_key(machine_id: str) -> str:
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as fh:
        sk = bytes.fromhex(fh.read().strip())
    pk = ed25519.publickey(sk)
    mid = _normalise(machine_id)
    sig = ed25519.signature(mid.encode("utf-8"), sk, pk)
    key = base64.b32encode(sig).decode("ascii").rstrip("=")
    return "-".join(key[i:i + 5] for i in range(0, len(key), 5))


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--new":
        generate_pair()
        return 0
    if not os.path.isfile(PRIVATE_KEY_PATH):
        print("ERROR: private key not found at", PRIVATE_KEY_PATH)
        print("Run 'python tools/keygen.py --new' to create one.")
        return 1

    machine_id = argv[0]
    key = make_key(machine_id)
    mid_norm = _normalise(machine_id)
    print("Machine ID :", "-".join(mid_norm[i:i + 5] for i in range(0, len(mid_norm), 5)))
    print("Product Key:", key)
    out = mid_norm + ".lic"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(key)
    print("License file written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
