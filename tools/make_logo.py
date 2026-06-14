"""One-off generator for the Zenith Soft brand logo and the app icon.

Run with:  python tools/make_logo.py
Outputs:   assets/logo.png  (brand badge)  and  assets/icon.ico (Windows icon)

The logo is drawn with QPainter so the project stays self-contained.
"""

from __future__ import annotations

import os
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen
)
from PyQt6.QtWidgets import QApplication

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "assets")


def _tooth_path(cx, cy, w, h) -> QPainterPath:
    hw = w / 2.0
    top = cy - h / 2.0
    bot = cy + h / 2.0
    p = QPainterPath()
    p.moveTo(cx - hw, top + h * 0.22)
    # left cusp
    p.cubicTo(cx - hw, top, cx - hw * 0.5, top, cx - hw * 0.28, top + h * 0.12)
    # central groove
    p.cubicTo(cx - hw * 0.10, top + h * 0.20, cx + hw * 0.10, top + h * 0.20,
              cx + hw * 0.28, top + h * 0.12)
    # right cusp
    p.cubicTo(cx + hw * 0.5, top, cx + hw, top, cx + hw, top + h * 0.22)
    # right shoulder
    p.cubicTo(cx + hw, top + h * 0.52, cx + hw * 0.72, top + h * 0.56,
              cx + hw * 0.52, top + h * 0.64)
    # right root
    p.cubicTo(cx + hw * 0.46, bot - h * 0.04, cx + hw * 0.32, bot,
              cx + hw * 0.20, bot)
    p.cubicTo(cx + hw * 0.11, bot, cx + hw * 0.07, bot - h * 0.20,
              cx, bot - h * 0.24)
    # left root
    p.cubicTo(cx - hw * 0.07, bot - h * 0.20, cx - hw * 0.11, bot,
              cx - hw * 0.20, bot)
    p.cubicTo(cx - hw * 0.32, bot, cx - hw * 0.46, bot - h * 0.04,
              cx - hw * 0.52, top + h * 0.64)
    p.cubicTo(cx - hw * 0.72, top + h * 0.56, cx - hw, top + h * 0.52,
              cx - hw, top + h * 0.22)
    p.closeSubpath()
    return p


def render_logo(size: int = 512) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    s = size
    # rounded badge with teal gradient
    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor("#0C2A33"))
    grad.setColorAt(1.0, QColor("#12B0A0"))
    badge = QRectF(s * 0.06, s * 0.06, s * 0.88, s * 0.88)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(badge, s * 0.22, s * 0.22)

    # subtle inner ring
    p.setPen(QPen(QColor(255, 255, 255, 38), s * 0.012))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(s * 0.12, s * 0.12, s * 0.76, s * 0.76),
                      s * 0.18, s * 0.18)

    # "ZS" monogram
    from PyQt6.QtGui import QFont, QFontDatabase
    fam = "Arial"
    # prefer the bundled Vazirmatn (has strong Latin glyphs) if available
    fonts_dir = os.path.join(ASSETS, "fonts")
    bold = os.path.join(fonts_dir, "Vazirmatn-Bold.ttf")
    if os.path.isfile(bold):
        fid = QFontDatabase.addApplicationFont(bold)
        fams = QFontDatabase.applicationFontFamilies(fid)
        if fams:
            fam = fams[0]
    font = QFont(fam, int(s * 0.30))
    font.setBold(True)
    font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 96)
    p.setFont(font)

    # soft shadow then white letters
    p.setPen(QColor(0, 0, 0, 55))
    p.drawText(QRectF(0, s * 0.025, s, s * 0.97),
               Qt.AlignmentFlag.AlignCenter, "ZS")
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "ZS")

    # small accent dot
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#7DEBDD"))
    p.drawEllipse(QPointF(s * 0.5, s * 0.78), s * 0.022, s * 0.022)

    p.end()
    return img


def main() -> int:
    app = QApplication(sys.argv)  # noqa: F841 — needed for QImage/QPainter
    os.makedirs(ASSETS, exist_ok=True)
    logo = render_logo(512)
    logo_path = os.path.join(ASSETS, "logo.png")
    logo.save(logo_path, "PNG")
    print("wrote", logo_path)

    # Build a multi-size .ico (use Pillow when available for proper ICO).
    ico_path = os.path.join(ASSETS, "icon.ico")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    try:
        from PIL import Image  # type: ignore
        import io
        buf = io.BytesIO()
        logo.save_data = None
        # convert QImage -> PNG bytes -> PIL
        ba = _qimage_png_bytes(logo)
        im = Image.open(io.BytesIO(ba)).convert("RGBA")
        im.save(ico_path, format="ICO",
                sizes=[(n, n) for n in sizes])
        print("wrote", ico_path, "(Pillow)")
    except Exception as exc:  # noqa: BLE001
        # Fallback: Qt ICO writer (single image)
        render_logo(256).save(ico_path, "ICO")
        print("wrote", ico_path, "(Qt fallback):", exc)
    # also a 256 png icon for the window
    render_logo(256).save(os.path.join(ASSETS, "icon.png"), "PNG")
    return 0


def _qimage_png_bytes(img: QImage) -> bytes:
    from PyQt6.QtCore import QBuffer, QByteArray
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(ba)


if __name__ == "__main__":
    raise SystemExit(main())
