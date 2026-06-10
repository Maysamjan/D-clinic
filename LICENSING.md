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

## Generating a key

On **your** computer (with `license_private/private_key.hex` present):

```bash
python tools/keygen.py A1B2C-D3E4F-5A6B7-C8D9E
```

Output:

```
Machine ID : A1B2C-D3E4F-5A6B7-C8D9E
Product Key: MFRGG-ZDFMZ-TWQ2L-K5...   (give this to the customer)
License file written: A1B2CD3E4F5A6B7C8D9E.lic
```

Send the customer **either** the `Product Key` text **or** the `.lic`
file. The key is long because it is a strong cryptographic signature; the
customer only pastes it once.

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

* Keys are **Ed25519 signatures** of the Machine ID. They cannot be forged
  without the private key, and a key made for one machine fails on any
  other machine.
* The stored activation (`data/license.dat`) is re-verified against the
  live hardware on **every start**, so copying the data folder does not
  bypass it.
* For maximum protection against tampering, distribute the app as a
  compiled Windows executable (see `BUILD.md`).
