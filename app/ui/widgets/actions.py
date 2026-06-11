"""Consistent, text-based action buttons for table "operations" columns.

Using clear Persian text labels (instead of emoji glyphs that may not be
present in the UI font) and a uniform soft-colored style keeps every table
neat and readable. Tables that host these widgets should use
:data:`ROW_HEIGHT` so the buttons are never clipped.
"""

from __future__ import annotations

from typing import Callable, Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ...services.i18n import t

# Row height that comfortably fits a row of action buttons.
ROW_HEIGHT = 50

_STYLE_OBJ = {
    "default": "ActBtn",
    "primary": "ActPrimary",
    "success": "ActSuccess",
    "warn": "ActWarn",
    "danger": "ActDanger",
}


def make_button(text: str, style: str = "default", tooltip: str = "",
                on_click: Callable[[], None] | None = None) -> QPushButton:
    btn = QPushButton(t(text))
    btn.setObjectName(_STYLE_OBJ.get(style, "ActBtn"))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(t(tooltip))
    if on_click is not None:
        btn.clicked.connect(lambda _checked=False: on_click())
    return btn


def actions_cell(buttons: Iterable[QPushButton]) -> QWidget:
    """Wrap action buttons in a neatly centred, evenly spaced row."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(8, 5, 8, 5)
    lay.setSpacing(6)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    for b in buttons:
        lay.addWidget(b)
    return w


def prepare_table(table) -> None:
    """Apply the action-row height to a table that hosts action buttons."""
    vh = table.verticalHeader()
    vh.setVisible(False)
    vh.setDefaultSectionSize(ROW_HEIGHT)
    vh.setMinimumSectionSize(ROW_HEIGHT)
