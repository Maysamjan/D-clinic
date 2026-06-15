# 🔐 D-Clinic — Product-Key Licensing (Vendor Guide)

This software is **locked to each computer**. A fresh installation will not
open until a valid **Product Key** for that exact machine is entered. Keys
can only be produced by **you, the vendor**, using your secret private key —
so copies of the installer cannot be activated by anyone else.

> ⚠️ **Keep `license_private/private_key.hex` secret.** Never put it in the
> installer, the ZIP you give customers, or any public place. Anyone with
> this file can generate valid keys. It is excluded from git on purpose.

---

## How activation works

1. The customer installs D-Clinic and runs it. The **Activation screen**
   appears and shows their **Machine ID**, e.g. `A1B2C-D3E4F-5A6B7-C8D9E`.
2. The customer sends you that Machine ID (phone, WhatsApp, etc.).
3. You generate a **Product Key** for it (below) and send it back — or send
   the `.lic` file.
4. The customer pastes the key (or loads the `.lic` file) and clicks
   **فعال‌سازی**. The app is now permanently activated **on that computer**.

If they copy the installation to another computer, the Machine ID changes,
so it asks for a new key — which only you can create.

---

## License types — DEMO and FULL

D-Clinic supports two kinds of license, both signed with your private key and
locked to one machine:

| | **FULL** | **DEMO** |
|---|---|---|
| Expiry | never | a date you choose (7 / 15 / 30 or custom days) |
| Patient limit | none | a cap you choose (e.g. 50) |
| Watermark on prints | none | `DEMO VERSION - ZENITH SOFT` on every page |
| About page | shows *Full (FULL)* | shows remaining days + patient quota |

The license terms are **inside the signed key** — the customer cannot extend
the expiry, raise the patient cap, or remove the watermark without a new key
that only you can produce.

### Generating a key

On **your** computer (with `license_private/private_key.hex` present):

```bash
# FULL (perpetual) — the default
python tools/keygen.py A1B2C-D3E4F-5A6B7-C8D9E
python tools/keygen.py --full A1B2C-D3E4F-5A6B7-C8D9E

# DEMO — expiring + patient-capped
python tools/keygen.py --demo --days 30 --max-patients 50  A1B2C-D3E4F-5A6B7-C8D9E
python tools/keygen.py --demo --days 7  --max-patients 20  A1B2C-D3E4F-5A6B7-C8D9E
python tools/keygen.py --demo --expiry 2026-09-01 --max-patients 100 A1B2C-...
```

Output (DEMO example):

```
Machine ID  : A1B2C-D3E4F-5A6B7-C8D9E
License type: DEMO
Expires on  : 2026-07-14 (30 days)
Patient cap : 50
Product Key : DCL2.RENI...   (give this to the customer)
License file written: A1B2CD3E4F5A6B7C8D9E.lic
```

Send the customer **either** the `Product Key` text **or** the `.lic`
file. The key is long because it is a strong cryptographic signature plus the
signed license terms; the customer only pastes it once.

> Renewing a DEMO: generate a new key (FULL, or a DEMO with a later date) for
> the same Machine ID. When the old demo expires the app shows a renewal
> screen where the customer pastes the new key.

---

## First-time setup of your key pair

A key pair already ships with this project (public key embedded in
`app/services/license_service.py`, private key delivered to you separately).
If you ever want a brand-new pair:

```bash
python tools/keygen.py --new
```

This writes a new `license_private/private_key.hex` and prints a new public
key. Paste that public key into `PUBLIC_KEY_HEX` in
`app/services/license_service.py`, then rebuild the app. (All previously
issued keys stop working after this.)

---

## Security notes

* Keys are **Ed25519 signatures**. A FULL key signs the Machine ID; a DEMO/FULL
  v2 key signs the full license payload (type, expiry, patient cap, Machine
  ID). They cannot be forged without the private key, and a key made for one
  machine fails on any other machine.
* The stored activation (`data/license.dat`) is re-verified against the
  live hardware on **every start**, so copying the data folder does not
  bypass it.
* **Clock-rollback protection:** the last run date (and the furthest date ever
  seen) is kept in a machine-bound, HMAC-protected `data/runstate.dat`. If the
  Windows clock is moved backwards past a small tolerance to dodge a DEMO
  expiry, the app detects it on the next start and **refuses to run** until the
  date is corrected. The file cannot be hand-edited because the HMAC key is
  derived from the machine fingerprint.
* **Backward compatibility:** legacy v1.0.0 keys (a bare base32 signature of
  the Machine ID) keep working and are treated as perpetual **FULL** licenses,
  so existing customers are never locked out.
* The whole system is **completely offline** — no server, no network calls.
* For maximum protection against tampering, distribute the app as a
  compiled Windows executable (see `BUILD.md`).
