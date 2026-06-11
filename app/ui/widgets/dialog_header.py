"""Styled header bar for dialogs, to give forms a clean, modern look."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout
)

from ...services.i18n import is_rtl, t as _t


def dialog_header(title: str, subtitle: str = "", icon: str = "") -> QFrame:
    """Return a teal gradient header bar with an optional icon and subtitle."""
    bar = QFrame()
    bar.setObjectName("DialogHeader")
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(12)

    if icon:
        ic = QLabel(icon)
        ic.setObjectName("DialogHeaderIcon")
        ic.setFixedSize(42, 42)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ic)

    text = QVBoxLayout()
    text.setSpacing(1)
    tl = QLabel(_t(title))
    tl.setObjectName("DialogHeaderTitle")
    text.addWidget(tl)
    if subtitle:
        s = QLabel(_t(subtitle))
        s.setObjectName("DialogHeaderSub")
        text.addWidget(s)
    lay.addLayout(text, 1)
    return bar


def setup_form_dialog(dialog: QDialog, title: str, subtitle: str = "",
                      icon: str = "") -> QVBoxLayout:
    """Give *dialog* a styled header + white body card.

    Returns the inner layout the caller adds the form and buttons to.
    """
    dialog.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if is_rtl()
        else Qt.LayoutDirection.LeftToRight)
    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    outer.addWidget(dialog_header(title, subtitle, icon))
    body = QFrame()
    body.setObjectName("DialogBody")
    outer.addWidget(body)
    inner = QVBoxLayout(body)
    inner.setContentsMargins(20, 18, 20, 18)
    inner.setSpacing(14)
    return inner
