"""Current-session state and role-based permission checks."""

from __future__ import annotations

from typing import Optional

from .. import config

# The currently logged-in user (dict) for the running application.
current_user: Optional[dict] = None


def login(user: dict) -> None:
    global current_user
    current_user = user


def logout() -> None:
    global current_user
    current_user = None


def role() -> str:
    return current_user["role"] if current_user else ""


def is_admin() -> bool:
    return role() == config.ROLE_ADMIN


def is_doctor() -> bool:
    return role() == config.ROLE_DOCTOR


def is_receptionist() -> bool:
    return role() == config.ROLE_RECEPTIONIST


# ---------------------------------------------------------------------------
# Capability matrix
# ---------------------------------------------------------------------------
# Capabilities map to UI sections / actions. Admin has everything.
_CAPABILITIES = {
    config.ROLE_ADMIN: {
        "dashboard", "patients", "patient_add", "patient_edit", "patient_delete",
        "visits", "visit_add", "payments", "payment_add", "invoices",
        "appointments", "expenses", "reports", "settings", "users", "services",
        "treatments_manage", "staff", "salaries", "inventory", "backup",
    },
    config.ROLE_DOCTOR: {
        "dashboard", "patients", "visits", "visit_add", "appointments",
        "reports", "inventory",
    },
    config.ROLE_RECEPTIONIST: {
        "dashboard", "patients", "patient_add", "patient_edit",
        "visits", "payments", "payment_add", "invoices", "appointments",
        "expenses", "inventory",
    },
}


def can(capability: str) -> bool:
    """Return True if the current user's role allows *capability*."""
    return capability in _CAPABILITIES.get(role(), set())
