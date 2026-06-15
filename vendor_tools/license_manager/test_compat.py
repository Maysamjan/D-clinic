"""Cross-verify that keys from this tool activate the real D-Clinic app.

Run:  python test_compat.py
"""

from __future__ import annotations

import datetime
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)      # tool modules (flat)
sys.path.insert(0, REPO)      # D-Clinic app package

import ed25519
import licensing_core as core
from app.services import license_service as lic  # the REAL app verifier


def main() -> int:
    # Use a throwaway key pair shared by the tool and the app verifier.
    sk = os.urandom(32)
    pk = ed25519.publickey(sk)
    keydir = tempfile.mkdtemp()
    with open(os.path.join(keydir, "private_key.hex"), "w") as fh:
        fh.write(sk.hex())
    core.private_key_path = lambda: os.path.join(keydir, "private_key.hex")
    lic._PUBLIC_KEY = pk  # app verifies against the same pair

    mid = "CB1036007C2FA0C6EF63"
    ok = True

    # DEMO 14 days / 50 patients
    res = core.generate_license(core.TYPE_DEMO, mid, days=14, max_patients=50)
    parsed = lic.parse_license(res["product_key"], mid=mid)
    demo_ok = (parsed is not None and parsed["type"] == "DEMO"
               and parsed["max_patients"] == 50
               and parsed["expiry_date"] == datetime.date.today() + datetime.timedelta(days=14))
    print("DEMO 14d/50 accepted by D-Clinic app:", demo_ok)
    ok &= demo_ok

    # FULL
    res = core.generate_license(core.TYPE_FULL, mid)
    parsed = lic.parse_license(res["product_key"], mid=mid)
    full_ok = (parsed is not None and parsed["type"] == "FULL"
               and parsed["expiry_date"] is None and parsed["max_patients"] == 0)
    print("FULL accepted by D-Clinic app:           ", full_ok)
    ok &= full_ok

    # Wrong machine must be rejected
    rejected = lic.parse_license(res["product_key"], mid="AAAAAAAAAAAAAAAAAAAA") is None
    print("Key rejected on a different machine:     ", rejected)
    ok &= rejected

    # Filename format
    fn = core.license_filename("Smile Dental", mid, "DEMO", 14)
    print("Filename:", fn)
    ok &= fn == "Smile_Dental_CB1036007C2FA0C6EF63_DEMO_14days.lic"

    print("\nRESULT:", "ALL COMPATIBILITY CHECKS PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
