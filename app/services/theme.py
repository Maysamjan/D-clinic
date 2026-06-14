"""Light / Dark theme engine.

The application stylesheet (``app/resources/styles.qss``) is authored as a
*template* with ``{{token}}`` placeholders. At runtime the active palette is
substituted in, so switching between **Light** and **Dark** mode is just a
matter of re-rendering the same template with a different palette and calling
``QApplication.setStyleSheet`` again — no restart required.

The teal brand accent and the dark sidebar are intentionally identical in both
modes so the product keeps a consistent identity; only the content surfaces
(window, cards, tables, inputs, dialogs) flip between light and dark.

RTL/LTR is independent of the theme and continues to be driven by the active
language, so Dari/Persian right-to-left layout is preserved in both modes.
"""

from __future__ import annotations

import os

from .. import config

LIGHT = "light"
DARK = "dark"

# Shared brand accent (identical in both themes).
ACCENT = "#0E9F8E"

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------
_PALETTES: dict[str, dict[str, str]] = {
    LIGHT: {
        "bg": "#EEF3F8",
        "surface": "#FFFFFF",
        "text": "#14253B",
        "muted": "#65788F",
        "border": "#E7EDF4",
        "gridline": "#EEF2F7",
        "input_bg": "#FFFFFF",
        "input_border": "#D4DEEA",
        "input_border_hover": "#B9C8DA",
        "input_focus_bg": "#FBFEFE",
        "secondary_bg": "#F1F5FA",
        "secondary_text": "#2A3B52",
        "secondary_hover": "#E6EDF5",
        "table_header_bg": "#F4F7FB",
        "sel_bg": "#E3F6F3",
        "sel_text": "#0A6B61",
        "dialog_bg": "#F4F7FB",
        "scrollbar": "#C7D3E0",
        "scrollbar_hover": "#A7B7C9",
        "tooltip_bg": "#14253B",
        "tooltip_fg": "#FFFFFF",
        "chip_bg": "#EEF3F8",
        "chip_text": "#51627A",
        # Custom-painted charts.
        "chart_bg": "#FFFFFF",
        "chart_grid": "#E6EBF2",
        "chart_text": "#64748B",
        "chart_value": "#0F2942",
    },
    DARK: {
        "bg": "#0F172A",
        "surface": "#1E293B",
        "text": "#E2E8F0",
        "muted": "#94A3B8",
        "border": "#334155",
        "gridline": "#2A3850",
        "input_bg": "#16233A",
        "input_border": "#3A4A62",
        "input_border_hover": "#4A5C76",
        "input_focus_bg": "#1B2C46",
        "secondary_bg": "#273449",
        "secondary_text": "#D7E0EC",
        "secondary_hover": "#31425C",
        "table_header_bg": "#172238",
        "sel_bg": "#0E3A36",
        "sel_text": "#5EEAD4",
        "dialog_bg": "#16223A",
        "scrollbar": "#3A4A62",
        "scrollbar_hover": "#4A5C76",
        "tooltip_bg": "#E2E8F0",
        "tooltip_fg": "#14253B",
        "chip_bg": "#273449",
        "chip_text": "#A8B6C8",
        # Custom-painted charts.
        "chart_bg": "#1E293B",
        "chart_grid": "#2F3E57",
        "chart_text": "#94A3B8",
        "chart_value": "#E2E8F0",
    },
}

# Process-wide active theme (mirrors the persisted clinic setting).
_active = LIGHT


def available() -> list[str]:
    return [LIGHT, DARK]


def get_theme() -> str:
    return _active


def set_theme(name: str) -> None:
    global _active
    _active = DARK if str(name).lower().startswith("d") else LIGHT


def is_dark() -> bool:
    return _active == DARK


def palette(name: str | None = None) -> dict[str, str]:
    return dict(_PALETTES.get(name or _active, _PALETTES[LIGHT]))


def color(token: str, name: str | None = None) -> str:
    """Return a single palette colour for the active (or named) theme."""
    return palette(name).get(token, "#000000")


def _template_path() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "resources", "styles.qss")
    return os.path.abspath(path)


def build_stylesheet(name: str | None = None) -> str:
    """Render the QSS template with the active (or named) palette."""
    try:
        with open(_template_path(), "r", encoding="utf-8") as fh:
            template = fh.read()
    except OSError:
        return ""
    pal = palette(name)
    pal.setdefault("accent", ACCENT)
    for token, value in pal.items():
        template = template.replace("{{" + token + "}}", value)
    return template
