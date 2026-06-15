# Zenith Soft License Manager — Vendor Guide

**CONFIDENTIAL — Zenith Soft only.** This tool, its database (`data/licenses.db`),
the `generated_licenses/` folder, and the private key **must never** be shared
with customers or placed in the D-Clinic customer installer/ZIP.

The License Manager is a desktop GUI for issuing D-Clinic **DEMO** and **FULL**
product keys without using the command line. Keys it produces are byte-for-byte
compatible with **D-Clinic v1.1.0** (verified by `test_compat.py`).

---

## 1. One-time setup

1. Install Python 3.10+ and the dependency:
   ```
   pip install -r requirements.txt
   ```
2. Put your vendor private key next to the tool:
   ```
   vendor_tools/license_manager/license_private/private_key.hex
   ```
   (The tool also finds it in the D-Clinic project root.) The window's top-right
   shows **🔐 Private key loaded** when it is found.
3. Run it:
   ```
   python license_manager.py
   ```
   …or run the built `LicenseManager.exe` (see §6).

> The private key **must match** the public key embedded in the D-Clinic app you
> ship (`app/services/license_service.py → PUBLIC_KEY_HEX`). Otherwise the app
> will reject every key.

---

## 2. Generate a 14-day demo license

1. Open the **Generate License** tab.
2. **Machine ID** — paste the ID from the customer's Activation screen
   (e.g. `CB103-6007C-2FA0C-6EF63`).
3. Optionally fill **Clinic Name**, **Customer Phone**, **City** (saved to history
   and used in the file name).
4. **License Type** → `DEMO`.
5. **DEMO days** → `14` (or 7 / 30 / Custom).
6. **Max patients** → `50` (or 100 / Unlimited / Custom).
7. Click **⚙ Generate License**.
8. The **Product Key** (starts with `DCL2.`) appears on the right. Use:
   - **📋 Copy Product Key** to copy the text, or
   - **📁 Open .lic folder** to open `generated_licenses/` and grab the `.lic` file.

The file is named e.g. `Smile_Dental_CB1036007C2FA0C6EF63_DEMO_14days.lic`.

---

## 3. Generate a full license

Same steps, but set **License Type** → `FULL`. There is **no expiry** and **no
patient limit**, and printed documents carry **no watermark**. The DEMO fields
are ignored. The file is named e.g. `Smile_Dental_CB1036007C2FA0C6EF63_FULL.lic`.

---

## 4. Send the license to the customer

Send **either**:
- the **Product Key** text (copy button) — the customer pastes it into the
  D-Clinic Activation screen, **or**
- the **`.lic` file** — the customer clicks *Load key file (.lic)* on the
  Activation screen.

Both are equivalent. The customer activates once; the key is locked to their
machine.

---

## 5. License history

The **License History** tab lists every key you have generated. You can:
- **Search** by clinic name, phone, or Machine ID;
- **Filter** by `DEMO` / `FULL`;
- **Copy Product Key** again (button or double-click a row);
- **Open .lic location** for the selected row.

History is stored locally in `data/licenses.db`.

---

## 6. Building the executable

From this folder on Windows:
```
build_license_manager.bat
```
This produces `dist\LicenseManager\LicenseManager.exe` and, if Inno Setup 6 is
installed, `Output\LicenseManager-Setup.exe`.

**After installing/copying the exe, place `license_private\private_key.hex`
next to it.** The build never bundles the private key.

---

## 7. What must NEVER be shared with customers

- `license_private/private_key.hex` (the signing key)
- This License Manager app / installer / `LicenseManager.exe`
- `data/licenses.db` (your customer history)
- The `generated_licenses/` folder

Customers only ever receive: the D-Clinic installer, and their own Product Key
(or `.lic` file).
