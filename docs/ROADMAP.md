# D-Clinic — Product Roadmap

**Vendor:** Zenith Soft
**Current version:** 1.0.0 (released 2026-06-14)

This roadmap outlines the planned direction for D-Clinic. It describes what each future release aims to deliver and the notable considerations involved. Items are grouped by target version.

---

## Version 1.1

### Advanced reporting

Expanded reporting with **custom date ranges** and deeper analytics, including **per-doctor** and **per-treatment** breakdowns, plus **exportable reports** for sharing or archiving outside the application. This gives clinic owners clearer insight into productivity and revenue across any period they choose. *Consideration:* report exports should preserve the bilingual (RTL/LTR) layout and Jalali dates used throughout D-Clinic.

### SMS / WhatsApp integration

Automated **appointment and recall reminders** delivered by SMS and/or WhatsApp, building on the existing Follow-up & Recall data. This reduces no-shows and helps bring patients back for unfinished treatment. *Consideration:* because the core application is offline-first, messaging requires connectivity to a provider/gateway, so this feature is designed as an optional, clearly bounded online capability with appropriate provider configuration.

### Multi-clinic support

Manage **multiple branches within a single installation**, with each branch's patients, staff, inventory, and finances organized together while still distinguishable. This suits owners running more than one location. *Consideration:* reporting and the dashboard will need branch-aware filtering, and licensing/activation scope for multi-branch installs will be defined as part of this work.

---

## Version 2.0

### LAN multi-user support

A **shared database across reception and doctor workstations** on the same local network, supporting **concurrent access** and **user presence** so several staff can work at once. This moves D-Clinic from single-workstation use to a true clinic-wide system. *Consideration:* concurrent access requires careful handling of record locking, conflict resolution, and a clear server/workstation setup, while remaining offline (LAN-only, no internet dependency).

### Cloud synchronization

**Optional, encrypted cloud backup and synchronization** across locations, allowing data to be safely backed up off-site and kept in sync between sites. This complements the existing local backup/restore. *Consideration:* this is opt-in and must protect patient data with strong encryption; the application remains fully usable offline, with cloud sync as an additive convenience rather than a requirement.

### Mobile companion app

A **mobile companion** for phones that lets staff **view the schedule**, perform **patient lookup**, and receive **reminders** on the go. This extends D-Clinic beyond the clinic desktop for quick reference. *Consideration:* the companion app pairs securely with the clinic system and exposes a limited, read-focused subset of functionality appropriate for mobile use.

---

## A note on priorities

This roadmap reflects current plans and may evolve. **Priorities and timing may shift based on customer feedback** and real-world needs gathered from clinics using D-Clinic. Features may be re-sequenced, expanded, or refined as we learn what delivers the most value.

---

*D-Clinic — Zenith Soft. Roadmap as of version 1.0.0.*
