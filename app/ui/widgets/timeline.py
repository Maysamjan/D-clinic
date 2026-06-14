"""Patient visit timeline widget (social-media style)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
)

from ...models import attachment as attachment_model
from ...utils import helpers
from ...services.i18n import t


class _TimelineItem(QFrame):
    """A single dated event in the timeline."""

    def __init__(self, visit: dict, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        # Marker column (dot + connecting line)
        marker = QWidget()
        marker.setFixedWidth(34)
        mlayout = QVBoxLayout(marker)
        mlayout.setContentsMargins(0, 6, 0, 0)
        mlayout.setSpacing(0)
        mlayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        dot = QLabel()
        dot.setFixedSize(16, 16)
        dot.setStyleSheet(
            "background-color: #2563eb; border: 3px solid #c7d9f7;"
            "border-radius: 8px;"
        )
        line = QFrame()
        line.setFixedWidth(2)
        line.setStyleSheet("background-color: #d3deec;")
        mlayout.addWidget(dot, 0, Qt.AlignmentFlag.AlignHCenter)
        mlayout.addWidget(line, 1, Qt.AlignmentFlag.AlignHCenter)

        # Card column
        card = QFrame()
        card.setObjectName("TimelineItem")
        clayout = QVBoxLayout(card)
        clayout.setContentsMargins(14, 12, 14, 12)
        clayout.setSpacing(4)

        header = QHBoxLayout()
        header.setDirection(QHBoxLayout.Direction.RightToLeft)
        date = QLabel("🗓  " + helpers.jalali_date(visit.get("visit_date")))
        date.setObjectName("TimelineDate")
        cost = QLabel(helpers.format_money(visit.get("cost", 0)))
        cost.setObjectName("TimelineCost")
        header.addWidget(date)
        header.addStretch(1)
        header.addWidget(cost)
        clayout.addLayout(header)

        title_text = visit.get("treatment_name") or "ویزیت"
        tooth = visit.get("tooth")
        if tooth:
            title_text += f" — دندان {tooth}"
        title = QLabel(title_text)
        title.setObjectName("TimelineTitle")
        clayout.addWidget(title)

        meta_parts = []
        if visit.get("doctor_name"):
            meta_parts.append("داکتر: " + visit["doctor_name"])
        atts = attachment_model.for_visit(visit["id"])
        if atts:
            meta_parts.append(f"📎 {helpers.format_money(len(atts), with_currency=False)} ضمیمه")
        if meta_parts:
            meta = QLabel("   •   ".join(meta_parts))
            meta.setObjectName("TimelineNotes")
            clayout.addWidget(meta)

        if visit.get("notes"):
            notes = QLabel(visit["notes"])
            notes.setObjectName("TimelineNotes")
            notes.setWordWrap(True)
            clayout.addWidget(notes)

        layout.addWidget(marker)
        layout.addWidget(card, 1)


class TimelineWidget(QScrollArea):
    """Scrollable timeline of all visits for a patient."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(8)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._container)

    def set_visits(self, visits: list[dict]):
        # Clear existing items
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not visits:
            empty = QLabel(t("هنوز هیچ ویزیتی برای این مریض ثبت نشده است."))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #94a3b8; padding: 30px;")
            self._layout.addWidget(empty)
            return

        # Newest first for a social-media feel
        for visit in sorted(visits, key=lambda v: (v.get("visit_date", ""), v["id"]),
                            reverse=True):
            self._layout.addWidget(_TimelineItem(visit))
        self._layout.addStretch(1)
