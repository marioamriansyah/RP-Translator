"""
Vector Icon Generator for PRORP Translator.

Generates crisp, resolution-independent minimalist vector icons programmatically via QPainter.
Guarantees zero blurriness at any Windows High-DPI scaling and zero emoji usage.
Seamlessly integrates the official RP+ brand logo and app icons.
"""

from __future__ import annotations

import os
import sys
import math
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QFont,
    QPolygonF, QBrush, QPainterPath
)

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_asset_path(filename: str) -> str | None:
    """
    Resolves the absolute path to an asset file across dev, PyInstaller, and installed environments.
    """
    candidates = []

    # 1. PyInstaller bundled directory (sys._MEIPASS in onefile/onedir)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "assets", filename))
        candidates.append(os.path.join(sys._MEIPASS, filename))

    # 2. Executable root and _internal directory (PyInstaller 6+ onedir)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "assets", filename))
        candidates.append(os.path.join(exe_dir, "_internal", "assets", filename))
        candidates.append(os.path.join(exe_dir, filename))

    # 3. Source tree root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(root_dir, "assets", filename))
    candidates.append(os.path.join(root_dir, "ui", "assets", filename))
    candidates.append(os.path.join(os.getcwd(), "assets", filename))

    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def get_app_qicon() -> QIcon:
    """
    Returns the official application QIcon directly from app_icon.ico
    (with full multi-resolution mipmaps for Windows taskbar & titlebar)
    or falls back to app_icon.png.
    """
    ico_path = get_asset_path("app_icon.ico")
    if ico_path:
        icon = QIcon(ico_path)
        if not icon.isNull():
            return icon

    png_path = get_asset_path("app_icon.png")
    if png_path:
        icon = QIcon(png_path)
        if not icon.isNull():
            return icon

    return QIcon(create_app_icon(32))


def get_vector_icon(name: str, color: str = "#FFFFFF", size: int = 16) -> QIcon:
    """
    Renders resolution-independent minimalist vector icons programmatically.
    Guarantees crisp, sharp lines at any Windows DPI scaling.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    qcolor = QColor(color)
    p_pen = QPen(qcolor, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(p_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name in ("guide", "guide_boxes"):
        # Minimalist 4-corner framing viewfinder
        r = 3.5
        # Top-left
        painter.drawLine(2, 2, int(2 + r), 2)
        painter.drawLine(2, 2, 2, int(2 + r))
        # Top-right
        painter.drawLine(14, 2, int(14 - r), 2)
        painter.drawLine(14, 2, 14, int(2 + r))
        # Bottom-left
        painter.drawLine(2, 14, int(2 + r), 14)
        painter.drawLine(2, 14, 2, int(14 - r))
        # Bottom-right
        painter.drawLine(14, 14, int(14 - r), 14)
        painter.drawLine(14, 14, 14, int(14 - r))
        # Subtle center crosshair
        p_sub = QPen(qcolor, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(p_sub)
        painter.drawLine(7, 8, 9, 8)
        painter.drawLine(8, 7, 8, 9)

    elif name == "position_osd":
        # Display monitor with floating overlay PIP
        painter.drawRoundedRect(1, 2, 14, 9, 1.5, 1.5)
        painter.drawLine(5, 14, 11, 14)
        painter.drawLine(8, 11, 8, 14)
        painter.setBrush(qcolor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(8, 4, 5, 4, 1, 1)

    elif name in ("setting", "settings", "gear"):
        # Precision 6-tooth gear matching Illustrator mockup
        cx, cy = 8.0, 8.0
        r_hub = 2.5
        r_base = 4.6
        r_outer = 6.6
        n = 6
        path = QPainterPath()
        step = 360 / (n * 2)
        for i in range(n * 2):
            deg = i * step
            rad = math.radians(deg)
            r = r_outer if (i % 2 == 0) else r_base
            x = cx + r * math.cos(rad)
            y = cy + r * math.sin(rad)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawEllipse(int(cx - r_hub), int(cy - r_hub), int(r_hub * 2), int(r_hub * 2))

    elif name == "snip_input":
        # Minimalist solid overlapping cards from Illustrator toolbar
        painter.setBrush(qcolor)
        painter.setPen(Qt.PenStyle.NoPen)
        # Back sheet
        painter.drawRoundedRect(5, 2, 8, 8, 1.5, 1.5)
        # Front sheet cutout
        painter.setBrush(QColor("#1E1F21"))
        painter.drawRoundedRect(2, 5, 9, 9, 2.0, 2.0)
        painter.setBrush(qcolor)
        painter.drawRoundedRect(3, 6, 7, 7, 1.5, 1.5)

    elif name == "snip_chat":
        # Minimalist chat speech bubble with lines from Illustrator toolbar
        painter.drawRoundedRect(2, 2, 12, 9, 2.5, 2.5)
        # Tail
        painter.drawLine(4, 11, 3, 14)
        painter.drawLine(3, 14, 7, 11)
        # Text line
        painter.drawLine(QPointF(5, 5.5), QPointF(11, 5.5))
        painter.drawLine(QPointF(5, 8.0), QPointF(9, 8.0))

    elif name == "clear":
        # [ ☒ Clear ] rounded square with crisp X
        p_clear = QPen(qcolor, 1.15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(p_clear)
        painter.drawRoundedRect(2, 2, 12, 12, 2.5, 2.5)
        painter.drawLine(5, 5, 11, 11)
        painter.drawLine(11, 5, 5, 11)

    elif name in ("translate", "chevron_right", "arrow_right"):
        # Crisp chevron arrow for circular action button
        p_arr = QPen(qcolor, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(p_arr)
        painter.drawLine(QPointF(6, 4.5), QPointF(10.5, 8))
        painter.drawLine(QPointF(10.5, 8), QPointF(6, 11.5))

    elif name == "copy":
        # Minimalist dual-sheet copy icon from Illustrator cards
        painter.setBrush(qcolor)
        painter.setPen(Qt.PenStyle.NoPen)
        # Back sheet
        painter.drawRoundedRect(5, 2, 8, 8, 1.5, 1.5)
        # Front sheet cutout
        painter.setBrush(QColor("#1E1F21"))
        painter.drawRoundedRect(2, 5, 9, 9, 2.0, 2.0)
        painter.setBrush(qcolor)
        painter.drawRoundedRect(3, 6, 7, 7, 1.5, 1.5)

    elif name == "check":
        # Crisp minimalist checkmark
        c_pen = QPen(qcolor, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(c_pen)
        painter.drawPolyline([QPointF(3, 8), QPointF(6, 11), QPointF(13, 4)])

    elif name == "save":
        painter.drawRoundedRect(2, 2, 12, 12, 2, 2)
        painter.drawLine(5, 2, 5, 6)
        painter.drawLine(11, 2, 11, 6)
        painter.drawLine(5, 6, 11, 6)
        painter.drawRoundedRect(4, 9, 8, 5, 1, 1)

    elif name == "search":
        painter.drawEllipse(3, 3, 7, 7)
        painter.drawLine(8, 8, 13, 13)

    elif name == "add":
        painter.drawLine(8, 3, 8, 13)
        painter.drawLine(3, 8, 13, 8)

    elif name == "edit":
        painter.drawLine(3, 13, 6, 13)
        painter.drawLine(3, 13, 3, 10)
        painter.drawLine(3, 10, 10, 3)
        painter.drawLine(10, 3, 13, 6)
        painter.drawLine(13, 6, 6, 13)

    elif name in ("theme", "palette"):
        painter.drawEllipse(2, 2, 12, 12)
        painter.setBrush(qcolor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(5, 5, 2, 2)
        painter.drawEllipse(8, 4, 2, 2)
        painter.drawEllipse(10, 7, 2, 2)
        painter.drawEllipse(6, 9, 2, 2)

    elif name in ("key", "api_key"):
        # Minimalist key icon
        painter.drawEllipse(3, 3, 6, 6)
        painter.drawLine(8, 7, 13, 12)
        painter.drawLine(11, 10, 13, 8)
        painter.drawLine(12, 11, 14, 9)

    elif name in ("external_link", "link"):
        # Arrow pointing top-right and corner frame
        painter.drawLine(8, 2, 14, 2)
        painter.drawLine(14, 2, 14, 8)
        painter.drawLine(7, 9, 13, 3)
        painter.drawPolyline([QPointF(11, 6), QPointF(11, 13), QPointF(3, 13), QPointF(3, 5), QPointF(10, 5)])

    elif name in ("eye", "show"):
        # Minimalist eye icon
        painter.drawArc(2, 4, 12, 8, 45 * 16, 90 * 16)
        painter.drawArc(2, 4, 12, 8, 225 * 16, 90 * 16)
        painter.drawEllipse(6, 6, 4, 4)

    elif name in ("eye_off", "hide"):
        # Minimalist eye with slash
        painter.drawArc(2, 4, 12, 8, 45 * 16, 90 * 16)
        painter.drawArc(2, 4, 12, 8, 225 * 16, 90 * 16)
        painter.drawLine(3, 3, 13, 13)

    painter.end()
    return QIcon(pixmap)


def create_rp_plus_logo(scale: float = 1.0, height: int = 28) -> QPixmap:
    """
    Renders the official RP+ brand logo using assets/logo.png.
    Falls back gracefully to vector drawing only if the asset file is not present.
    """
    target_h = int(height * scale)
    logo_path = get_asset_path("logo.png")
    if logo_path:
        pm = QPixmap(logo_path)
        if not pm.isNull() and pm.height() > 0:
            return pm.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)

    # Fallback procedural vector drawing if file is missing
    w = int(120 * scale)
    h = int(28 * scale)
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy = 14 * scale, 14 * scale
    r_outer = 11 * scale
    r_inner = 6 * scale

    outer_pts = []
    inner_pts = []
    for deg in [30, 90, 150, 210, 270, 330]:
        rad = math.radians(deg)
        outer_pts.append(QPointF(cx + r_outer * math.cos(rad), cy + r_outer * math.sin(rad)))
        inner_pts.append(QPointF(cx + r_inner * math.cos(rad), cy + r_inner * math.sin(rad)))

    hex_pen = QPen(QColor("#FFFFFF"), 2.5 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin)
    painter.setPen(hex_pen)
    painter.drawPolygon(QPolygonF(outer_pts))

    inner_pen = QPen(QColor("#FFFFFF"), 1.5 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.MiterJoin)
    painter.setPen(inner_pen)
    painter.drawPolygon(QPolygonF(inner_pts))

    font = QFont("Segoe UI", int(14 * scale), QFont.Weight.Black)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2 * scale)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))

    text_x = int(32 * scale)
    text_rect = pixmap.rect().adjusted(text_x, 0, 0, 0)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "RP+")

    painter.end()
    return pixmap


def create_app_icon(size: int = 32) -> QPixmap:
    """
    Generate brand icon for window, dialogs, and controls using assets/app_icon.png.
    """
    for name in ("app_icon.png", "app_icon.ico"):
        icon_path = get_asset_path(name)
        if icon_path:
            pm = QPixmap(icon_path)
            if not pm.isNull() and pm.width() > 0:
                return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(20, 21, 23))
    painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
    painter.drawRoundedRect(2, 2, size - 4, size - 4, 8, 8)

    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI", int(size * 0.35), QFont.Weight.Black)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "RP+")
    painter.end()
    return pixmap
