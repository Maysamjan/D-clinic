# D-Clinic — Vendor Licensing Guide (Zenith Soft Internal)

**Audience:** Zenith Soft staff only.
**Confidentiality:** This document and the licensing tooling it describes are **internal to Zenith Soft** and must not be shared with customers.

---

## 1. Overview

D-Clinic uses **per-machine, offline activation** based on **Ed25519** digital signatures.

- A **public key** is embedded in every shipped copy of the application. The app uses it to verify that a Product Key is genuine and valid for the machine.
- A **private key** is held **only by Zenith Soft**. It is used to sign Product Keys. It is never shipped, never given to customers, and never committed to source control.

Because verification is done with the embedded public key, activation works **fully offline** on the customer's machine. No license server or internet connection is involved.

---

## 2. How activation works (end to end)

1. **Customer installs and launches D-Clinic.** On first run, the **Activation screen** shows a unique **Machine ID** for that computer.
2. **Customer sends their Machine ID** to Zenith Soft (phone, message, or email).
3. **Vendor generates a Product Key** for that exact Machine ID using the keygen tool (see Section 3).
4. **Vendor delivers the Product Key** to the customer (see Section 4).
5. **Customer enters the Product Key** on the Activation screen. The app verifies the Ed25519 signature against the embedded public key and confirms the key matches this machine's Machine ID.
6. On success, activation completes, the **Customer Registration** form is shown (Clinic Name, Doctor Name, Phone, City), and the app becomes usable.

A Product Key is bound to a single Machine ID. It will not activate any other computer.

---

## 3. Generating a Product Key

Run the keygen tool, which reads the vendor's private key and signs the customer's Machine ID:

```
python tools/keygen.py
```

- The tool reads the private key from **`license_private/private_key.hex`**.
- It takes the customer's **Machine ID** as input and produces a signed **Product Key** for that machine.

> **Requirement:** `tools/keygen.py` and the `license_private/private_key.hex` file are part of the **vendor-only** toolchain. They must be present only on Zenith Soft's secure machine(s) where keys are generated.

---

## 4. Delivering the Product Key

Deliver the generated key to the customer in either form:

- A **`.lic` file** the customer loads/enters on the Activation screen, or
- The **Product Key as text** (sent by message or email) that the customer pastes into the Activation screen.

Confirm with the customer that the key activates successfully. Remind them that the key is valid only for the machine whose Machine ID they provided.

---

## 5. CRITICAL security rules

These rules protect the entire licensing scheme. A leak of the private key would let anyone forge valid Product Keys for any machine.

1. **The private key (`license_private/private_key.hex`) must NEVER be shipped to customers.** Only the embedded **public** key goes into the application that customers receive.
2. **The private key must NEVER be committed to git** (or any version control or shared/cloud storage that could expose it). Keep it out of the repository — for example via `.gitignore` — and verify it is not present in any build artifact.
3. **The keygen tool and the private key go only to the vendor.** `tools/keygen.py` together with `license_private/private_key.hex` stay on Zenith Soft's secure systems and are never bundled into customer installers.
4. **Restrict access.** Limit who at Zenith Soft can access the private key and keygen tooling. Store the private key securely (e.g., access-controlled storage with an offline backup).
5. **Never expose the private key in logs, screenshots, or support sessions.**

> **Reminder:** Customers only ever need (a) the installed application, which contains the public key, and (b) a Product Key for their Machine ID. They never need and must never receive the private key or the keygen tool.

---

## 6. Rotating keys if compromised

If you suspect the private key has been exposed, leaked, or otherwise compromised, rotate the key pair:

1. **Generate a new Ed25519 key pair** (new private key + new public key) on a secure machine.
2. **Replace the embedded public key** in the application with the new public key and produce a **new application build/release**.
3. **Securely store the new private key** as `license_private/private_key.hex`, applying all rules in Section 5, and securely destroy/retire the compromised private key.
4. **Re-issue Product Keys** for active customers as they update to the new build. Product Keys signed with the old (compromised) private key will no longer verify against the new public key, so customers on the new build need keys signed with the new private key.
5. **Plan the customer transition** so clinics are not left unable to activate — coordinate the new build and the re-issued keys together.

> **Note:** Rotation invalidates previously issued keys against the new build by design. Communicate clearly with affected customers and have replacement keys ready before distributing the new build.

---

*D-Clinic — Zenith Soft. Internal licensing guide. Version 1.0.0.*
