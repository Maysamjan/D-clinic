"""Dashboard statistic card widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout
)


class StatCard(QFrame):
    """A coloured icon + value + label card for the dashboard."""

    def __init__(self, title: str, value: str, icon: str = "•",
                 accent: str = "#2563eb", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setMinimumHeight(110)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(15, 41, 66, 35))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        icon_box = QLabel(icon)
        icon_box.setFixedSize(54, 54)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet(
            f"background-color: {accent}1f; color: {accent};"
            f"border-radius: 14px; font-size: 24px; font-weight: bold;"
        )

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        title_label = QLabel(title)
        title_label.setObjectName("StatLabel")
        text_box.addWidget(self.value_label)
        text_box.addWidget(title_label)

        layout.addLayout(text_box, 1)
        layout.addWidget(icon_box)

    def set_value(self, value: str):
        self.value_label.setText(value)
