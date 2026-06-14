# D-Clinic — Zenith Soft

**Dental Clinic Management System**
**Version 1.0.0**
**User Manual**

---

*Published by Zenith Soft. This manual covers the installation, activation, and day-to-day use of D-Clinic version 1.0.0. Screens and labels appear in your selected interface language (Persian/Dari or English).*

---

## Table of Contents

1. [Introduction & System Requirements](#1-introduction--system-requirements)
2. [Installation](#2-installation)
3. [First-Run Activation & Customer Registration](#3-first-run-activation--customer-registration)
4. [Logging In & User Roles](#4-logging-in--user-roles)
5. [Dashboard Overview](#5-dashboard-overview)
6. [Managing Patients](#6-managing-patients)
7. [The Patient File](#7-the-patient-file)
8. [Using the Dental Chart](#8-using-the-dental-chart)
9. [Creating a Treatment Plan](#9-creating-a-treatment-plan)
10. [Recording Visits & Attachments](#10-recording-visits--attachments)
11. [Follow-up & Recall](#11-follow-up--recall)
12. [Prescriptions](#12-prescriptions)
13. [Payments & Invoices](#13-payments--invoices)
14. [Appointments](#14-appointments)
15. [Staff & Salaries](#15-staff--salaries)
16. [Inventory](#16-inventory)
17. [Expenses & Accounting](#17-expenses--accounting)
18. [Reports & Printing](#18-reports--printing)
19. [Settings](#19-settings)
20. [Backup & Restore](#20-backup--restore)
21. [Troubleshooting / FAQ](#21-troubleshooting--faq)
22. [Support Contact](#22-support-contact)

---

## 1. Introduction & System Requirements

D-Clinic is a complete, fully offline management system for dental clinics. It keeps a permanent file for every patient, manages appointments, treatment plans, prescriptions, payments, inventory, staff payroll, and accounting, and produces professional printed documents. The interface is bilingual: Persian/Dari (right-to-left) and English (left-to-right), and all dates use the Jalali (Solar Hijri) calendar.

### Key characteristics

- **Fully offline** — no internet connection is required to use the program at any time.
- **Single installation per machine** — the software is activated and licensed to one computer.
- **Bilingual interface** — switch between Persian/Dari and English at any time.
- **Jalali calendar** — all dates throughout the program follow the Solar Hijri calendar.

### System requirements

| Item | Requirement |
| --- | --- |
| Operating system | Windows 8, Windows 10, or Windows 11 |
| Internet | Not required |
| Disk space | A few hundred megabytes free, plus space for attachments (X-rays, photos, PDFs) |
| Display | 1366×768 or higher recommended |
| Printer | Any A4 printer for printing documents (optional) |

> **Tip:** Although no internet is needed to run D-Clinic, you should keep your computer's date and time correct, because all records and reports are timestamped.

---

## 2. Installation

1. Obtain the D-Clinic installer from Zenith Soft.
2. Double-click the installer file and follow the on-screen prompts.
3. Accept the destination folder (or choose your own) and complete the installation.
4. Once installed, a D-Clinic shortcut is placed on the Desktop and in the Start menu.

**Where your data is stored:** Installed builds keep all clinic data in:

```
C:\ProgramData\Zenith Soft\D-Clinic\
```

This folder holds the database, attachments, and automatic backups. Do not delete or move it.

> **Tip:** If you ever move to a new computer, install D-Clinic there and use the **Restore** feature (see Section 20) to bring your data across. A new machine requires a new activation (see Section 3).

---

## 3. First-Run Activation & Customer Registration

D-Clinic uses a secure, per-machine, offline activation. No internet connection is involved — activation is done with a Product Key supplied by Zenith Soft.

### Activating the software

1. Launch D-Clinic for the first time. The **Activation screen** appears.
2. The screen shows a unique **Machine ID** for this computer.
3. Send your Machine ID to Zenith Soft (by phone, message, or email).
4. Zenith Soft generates a **Product Key** that is valid only for your machine and sends it back to you.
5. Enter (or paste) the Product Key into the activation screen and confirm.
6. If the key is valid for this machine, activation succeeds and you may continue.

> **Note:** A Product Key is tied to one specific computer. It will not activate a different machine. If you change computers, request a new key for the new Machine ID.

### Customer registration

After successful activation, a one-time **Customer Registration** form collects your clinic details:

- **Clinic Name**
- **Doctor Name**
- **Phone**
- **City**

These details are used on printed documents (invoices, prescriptions, reports) and on the About page. You can update them later in **Settings**.

---

## 4. Logging In & User Roles

After activation, the **Login** screen appears each time you start the program.

### Default login

The factory default account is:

- **Username:** `admin`
- **Password:** `admin`

> **Important:** Change the default password immediately after first login (see Section 19, *Settings → Password change*). Leaving the default password is a security risk.

### User roles

D-Clinic supports role-based permissions. Each user is assigned one role:

| Role | Typical access |
| --- | --- |
| **Admin** | Full access to all modules, including settings, staff, accounting, backup, and user management. |
| **Doctor** | Clinical work — patients, dental charts, treatment plans, visits, prescriptions; viewing schedules. |
| **Receptionist** | Front-desk work — patient registration, appointments, payments, invoices. |

The menus and actions you see depend on your role. If an option is not visible, your role may not have permission for it.

---

## 5. Dashboard Overview

The Dashboard is the home screen after login. It gives you an at-a-glance view of the clinic.

### Stat cards

- **Today's patients**
- **Today's appointments**
- **New registrations**
- **Total patients**
- **Today's revenue**
- **Monthly revenue**
- **Outstanding balances**

### Charts

- **Revenue chart** — revenue over time.
- **Patient growth chart** — how your patient base is growing.
- **Common treatments chart** — your most frequently performed treatments.

### Follow-up & Recall panel

A dedicated panel lists:

- Patients **due for follow-up** (recall dates that have arrived).
- Patients with **unfinished treatment plans**.

> **Tip:** Start each day on the Dashboard to see who needs a recall call and what revenue is outstanding.

---

## 6. Managing Patients

Every patient has one permanent file in D-Clinic.

### Registering a new patient

1. Open the **Patients** section.
2. Click **New Patient**.
3. Enter personal information (name, phone, etc.).
4. Enter medical information: **allergies**, **medical history**, and **blood type**.
5. Save. The patient receives an automatic code in the form **P-000001**.

> **Allergy alert:** If a patient has recorded allergies, an **allergy alert banner** appears prominently in their file so it is never missed.

### Searching for a patient

Use the search box to find a patient by **name**, **phone**, or **patient code**.

> **Tip:** Patient codes are sequential and permanent (P-000001, P-000002, …). They never change, which makes them reliable references on paper documents.

---

## 7. The Patient File

Opening a patient shows their complete file, organized into tabs:

| Tab | What it contains |
| --- | --- |
| **Overview & Timeline** | Summary of the patient plus a chronological timeline of activity. |
| **Dental Chart** | The interactive odontogram (see Section 8). |
| **Visits / Treatments** | All recorded visits and treatments (see Section 10). |
| **Treatment Plan** | Planned future treatments (see Section 9). |
| **Prescriptions** | Saved prescriptions for the patient (see Section 12). |
| **Payments** | Payment history and balances (see Section 13). |
| **Invoices** | Generated invoices (see Section 13). |
| **Files / Attachments** | Stored files such as X-rays, photos, and PDFs. |

> **Tip:** The Overview & Timeline tab is the fastest way to understand a patient's history before they sit in the chair.

---

## 8. Using the Dental Chart

The Dental Chart (odontogram) is an interactive map of the mouth.

### What it shows

- **32 permanent teeth** drawn as two anatomical arches (upper and lower), using **FDI numbering**.
- A readable **legend** explaining each color.

### Setting a tooth condition

1. Open the patient's **Dental Chart** tab.
2. **Click a tooth** on the chart.
3. Choose its condition:
   - Healthy
   - Caries
   - Filling
   - Root Canal
   - Crown
   - Implant
   - Extracted
   - Missing
4. The tooth is **color-coded** according to its condition.

Each tooth also keeps its **per-tooth treatment history**, so you can see what was done to a specific tooth over time.

> **Tip:** Update the chart as you work so it always reflects the current state of the patient's mouth.

---

## 9. Creating a Treatment Plan

The Treatment Plan module lets doctors prepare a patient's future treatment.

1. Open the patient's **Treatment Plan** tab.
2. Add a plan line with:
   - **Tooth number**
   - **Planned treatment**
   - **Estimated cost**
   - **Status**
   - **Notes**
3. Repeat for each planned item.
4. Save the plan.

You can print a professional **treatment plan** to give to the patient (see Section 18).

> **Tip:** Patients with unfinished treatment plans appear in the Dashboard's Follow-up & Recall panel, helping you bring them back to complete their care.

---

## 10. Recording Visits & Attachments

A visit records a single appointment's clinical and financial activity.

### Recording a visit

1. Open the patient's **Visits / Treatments** tab and click **New Visit**.
2. Fill in:
   - **Date**
   - **Doctor / provider**
   - **Treatment type**
   - **Tooth**
   - **Cost**
   - **Notes**
3. Optionally attach files such as **X-rays, photos, or PDFs**.
4. Optionally set a **Next Visit (recall) date**.
5. Save.

> **Tip:** Setting a Next Visit date automatically feeds the Follow-up & Recall list, so the patient is flagged when the recall date arrives.

---

## 11. Follow-up & Recall

D-Clinic helps you keep patients coming back.

- Patients with a **recall date** that has arrived appear in the **Follow-up & Recall** panel on the Dashboard.
- Patients with **unfinished treatment plans** also appear there.

Use this list to call patients and schedule them. Recall dates are set when recording a visit (Section 10).

> **Note:** Version 1.0.0 does not send automatic SMS or WhatsApp reminders. Reminders are handled by reviewing this list and contacting patients directly. Automated reminders are on the roadmap.

---

## 12. Prescriptions

Prescriptions are fully editable and saved per patient.

1. Open the patient's **Prescriptions** tab and start a new prescription.
2. Add each drug with:
   - **Drug name** (English drug names)
   - **Dosage**
   - **Dispense quantity**
   - **Instructions**
3. Save the prescription to the patient's file.
4. **Print** a professional prescription (see Section 18).

> **Tip:** Because prescriptions are saved per patient, you can reopen and reprint a previous prescription at any time.

---

## 13. Payments & Invoices

### Payments

The **Payments** tab records what a patient has paid and tracks balances. Outstanding balances roll up to the Dashboard's *Outstanding balances* card.

### Invoices

The **Invoices** tab generates invoices for the patient. Invoices can be **printed** on professional A4 layouts that include your clinic logo and details (see Section 18).

> **Tip:** Use the **daily cash report** (Section 18) to reconcile the day's payments.

---

## 14. Appointments

The Appointments module is used to schedule patient visits.

1. Open the **Appointments** section.
2. Create an appointment for a patient with the desired date and time.
3. View the schedule to plan the clinic's day.

> **Tip:** Today's appointments are summarized on the Dashboard so the front desk always sees the day ahead.

---

## 15. Staff & Salaries

D-Clinic includes a staff/doctor registry with payroll.

- Maintain a registry of **staff and doctors**.
- Record **payroll** details: **salary** and/or **commission**.
- Generate and **print salary receipts** on professional layouts.

> **Tip:** Commission-based providers can be linked to the visits they perform, supporting accurate payroll.

---

## 16. Inventory

The Inventory (store) module manages your clinic's supplies.

- Track **medicines, equipment, and consumables**.
- Record **stock in** and **stock out**.
- Stay aware of **low stock** and **expiry**.

> **Tip:** Review low-stock and expiry awareness regularly so you reorder before you run out and discard expired items on time.

---

## 17. Expenses & Accounting

The accounting module tracks the financial health of the clinic.

- Record **expenses**.
- View **profit and loss** based on revenue versus expenses.
- Maintain a **service price list** used across the program.

> **Tip:** Keeping the service price list current means estimated costs in treatment plans and invoices stay accurate.

---

## 18. Reports & Printing

D-Clinic produces professional **A4** documents with proper **RTL/LTR** layouts, including your **clinic logo and details**. Printable documents include:

- **Patient file**
- **Single visit**
- **Invoice**
- **Prescription**
- **Treatment plan**
- **Salary receipt**
- **Daily cash report**

To print, open the relevant record and choose the print option. The document is laid out in your selected language direction (right-to-left for Persian/Dari, left-to-right for English).

> **Tip:** Add your clinic logo and full details in **Settings** so every printout looks complete and professional.

---

## 19. Settings

The **Settings** section lets you configure the program.

### Clinic information

Set or update:

- Clinic **name**
- **Doctor / owner**
- **Phone**
- **City**
- **Address**
- **Email**
- **Logo**

These details appear on printed documents and the About page.

### Switching the interface language

1. Open **Settings**.
2. Choose the **UI language**: Persian/Dari or English.
3. The interface updates to the selected language and text direction.

### Changing your password

1. Open **Settings**.
2. Choose **Password change**.
3. Enter your current password and your new password, then confirm.

> **Important:** Change the default `admin` password the first time you log in.

---

## 20. Backup & Restore

Protecting your data is essential. D-Clinic provides several backup options.

### Backup

- **Automatic daily backup** — runs automatically to protect your data every day.
- **Manual backup** — create a backup on demand.
- **Export to chosen location** — save a backup copy to a location you choose (for example, an external drive).

### Restore

- **Restore from file** — restore your data from a backup file. Before restoring, D-Clinic makes a **safety copy** of the current data, so a restore can be undone if needed.

> **Tip:** Regularly export a backup to an external drive or USB stick and keep it in a safe place. Installed builds store data and automatic backups in `C:\ProgramData\Zenith Soft\D-Clinic\`.

---

## 21. Troubleshooting / FAQ

**The Activation screen keeps appearing / my key won't activate.**
A Product Key is valid only for the Machine ID shown on this computer. Confirm you sent the correct Machine ID and entered the exact key you received. If you changed computers or hardware, request a new key from Zenith Soft.

**I forgot the admin password.**
Contact Zenith Soft support. Keep your password safe and change it from the default after first login.

**Do I need an internet connection?**
No. D-Clinic is fully offline. Activation also works without internet, using the Product Key supplied by the vendor.

**The dates look unfamiliar.**
D-Clinic uses the Jalali (Solar Hijri) calendar throughout.

**My printouts are missing the logo or clinic details.**
Add your clinic information and logo in **Settings**.

**A menu option I expected is missing.**
Your user role may not have permission for it. Admin accounts have the broadest access.

**How do I move to a new computer?**
Install D-Clinic on the new computer, activate it with a new Product Key for that machine's Machine ID, then **Restore** your data from a backup file.

**Where is my data kept?**
In `C:\ProgramData\Zenith Soft\D-Clinic\` for installed builds.

---

## 22. Support Contact

For help with activation, restoring data, or any question about D-Clinic, contact Zenith Soft support:

- **Support phone:** _[to be filled by vendor]_
- **Support email:** _[to be filled by vendor]_

When contacting support about activation, please have your **Machine ID** ready.

---

*D-Clinic — Zenith Soft. Version 1.0.0.*
