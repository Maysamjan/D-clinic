#!/usr/bin/env python3
"""D-Clinic — Vendor Product-Key Generator (KEEP PRIVATE).

⚠️  This tool and the private key file are for the SOFTWARE VENDOR ONLY.
    Never ship them to customers. Anyone holding the private key can
    generate valid product keys.

Usage
-----
A customer installs D-Clinic and reads their **Machine ID** from the
activation screen (e.g. ``A1B2C-D3E4F-5A6B7-C8D9E``). They send it to you.

Generate a **FULL** (perpetual, no limits, no watermark) license:

    python tools/keygen.py A1B2C-D3E4F-5A6B7-C8D9E
    python tools/keygen.py --full A1B2C-D3E4F-5A6B7-C8D9E

Generate a **DEMO** license (expiring, patient-capped, watermarked):

    python tools/keygen.py --demo --days 30  --max-patients 50  A1B2C-...
    python tools/keygen.py --demo --days 7   --max-patients 20  A1B2C-...
    python tools/keygen.py --demo --expiry 2026-09-01 --max-patients 100 A1B2C-...

Common DEMO durations are 7, 15 or 30 days; pass any custom value with
``--days`` or an absolute date with ``--expiry``. ``--max-patients 0`` means
no patient cap.

It prints the **Product Key** to give back to the customer, and also writes
a ``<machine-id>.lic`` file they can simply load on the activation screen.

The private key is read from ``license_private/private_key.hex`` (kept out
of the repository). Generate a new key pair with ``--new`` if you ever need
one (then update PUBLIC_KEY_HEX in app/services/license_service.py).
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import ed25519  # noqa: E402
from app.services import license_service as lic  # noqa: E402

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
    print()
    print("!" * 70)
    print("ACTION REQUIRED: paste the public key below into")
    print("    app/services/license_service.py  ->  PUBLIC_KEY_HEX")
    print("and REBUILD the app. Until you do, the app will REJECT every key")
    print("this private key produces. (All previously issued keys also stop")
    print("working after generating a new pair.)")
    print("!" * 70)
    print(pk.hex())


def _load_private() -> bytes:
    with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as fh:
        return bytes.fromhex(fh.read().strip())


def _check_pair_matches_app() -> None:
    """Abort if the private key does not match the app's embedded public key.

    This is the #1 cause of "keygen runs but the app rejects the key": the
    private key in license_private/private_key.hex was regenerated (e.g. with
    --new) without pasting the new public key into license_service.py, so every
    key the app verifies fails. We catch it here, before issuing a bad key.
    """
    pk = ed25519.publickey(_load_private())
    if pk.hex().lower() != lic.PUBLIC_KEY_HEX.lower():
        print("=" * 70)
        print("ERROR: key-pair mismatch — the app would REJECT every key from")
        print("this private key, because it does not match the public key")
        print("embedded in app/services/license_service.py.")
        print()
        print("Your private key's public key is:")
        print("    " + pk.hex())
        print()
        print("The app currently expects PUBLIC_KEY_HEX =")
        print("    " + lic.PUBLIC_KEY_HEX)
        print()
        print("FIX (choose one):")
        print("  • Use the ORIGINAL private key that matches the shipped app, OR")
        print("  • Paste the public key above into PUBLIC_KEY_HEX in")
        print("    app/services/license_service.py and REBUILD the app, so the")
        print("    app and your keys use the same key pair.")
        print("=" * 70)
        raise SystemExit(2)


def make_token(machine_id: str, license_type: str, expiry: datetime.date | None,
               max_patients: int) -> str:
    """Build a signed v2 product key for the given machine and terms."""
    sk = _load_private()
    pk = ed25519.publickey(sk)
    mid = _normalise(machine_id)
    issue = datetime.date.today().strftime("%Y%m%d")
    expiry_str = expiry.strftime("%Y%m%d") if expiry else ""
    payload = lic.build_payload(license_type, mid, issue, expiry_str, max_patients)
    sig = ed25519.signature(payload.encode("utf-8"), sk, pk)
    return lic.make_token(payload, sig)


def _resolve_expiry(args) -> datetime.date | None:
    if args.expiry:
        return datetime.date.fromisoformat(args.expiry)
    if args.days:
        return datetime.date.today() + datetime.timedelta(days=args.days)
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="D-Clinic vendor product-key generator",
        add_help=True)
    parser.add_argument("machine_id", nargs="?",
                        help="Machine ID from the activation screen")
    parser.add_argument("--new", action="store_true",
                        help="generate a brand-new key pair")
    parser.add_argument("--full", action="store_true",
                        help="issue a perpetual FULL license (default)")
    parser.add_argument("--demo", action="store_true",
                        help="issue an expiring DEMO license")
    parser.add_argument("--days", type=int,
                        help="DEMO validity in days (e.g. 7, 15, 30)")
    parser.add_argument("--expiry", type=str,
                        help="DEMO absolute expiry date, YYYY-MM-DD")
    parser.add_argument("--max-patients", type=int, default=0,
                        help="DEMO patient cap (0 = unlimited)")
    args = parser.parse_args(argv)

    if args.new:
        generate_pair()
        return 0

    if not args.machine_id:
        parser.print_help()
        return 0

    if not os.path.isfile(PRIVATE_KEY_PATH):
        print("ERROR: private key not found at", PRIVATE_KEY_PATH)
        print("Run 'python tools/keygen.py --new' to create one.")
        return 1

    # Fail fast if this private key won't match the app's embedded public key.
    _check_pair_matches_app()

    license_type = lic.TYPE_DEMO if args.demo else lic.TYPE_FULL
    expiry = None
    if license_type == lic.TYPE_DEMO:
        expiry = _resolve_expiry(args)
        if expiry is None:
            print("ERROR: a DEMO license needs --days or --expiry.")
            return 1

    token = make_token(args.machine_id, license_type, expiry, args.max_patients)
    mid_norm = _normalise(args.machine_id)

    print("Machine ID  :",
          "-".join(mid_norm[i:i + 5] for i in range(0, len(mid_norm), 5)))
    print("License type:", license_type)
    if license_type == lic.TYPE_DEMO:
        print("Expires on  :", expiry.isoformat(),
              f"({(expiry - datetime.date.today()).days} days)")
        cap = args.max_patients or 0
        print("Patient cap :", cap if cap > 0 else "unlimited")
    print("Product Key :", token)

    out = mid_norm + ".lic"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(token)
    print("License file written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
