# vendor_tools/ — VENDOR-ONLY (do not ship to customers)

Everything under `vendor_tools/` is for **Zenith Soft (the software owner)**
only. It is **excluded from the D-Clinic customer build** (the D-Clinic
PyInstaller spec only bundles `app/`, `assets/` and the stylesheet) and must
**never** be placed in a customer installer or ZIP.

## Contents

| Folder | What it is |
|---|---|
| `license_manager/` | **Zenith Soft License Manager** — a PyQt6 desktop app to generate DEMO/FULL D-Clinic product keys with a searchable history. See `license_manager/VENDOR_GUIDE.md`. |

## Never share with customers

- `license_private/private_key.hex` (the signing key)
- the License Manager app / `LicenseManager.exe`
- `license_manager/data/licenses.db` (customer history)
- `license_manager/generated_licenses/` (issued `.lic` files)
