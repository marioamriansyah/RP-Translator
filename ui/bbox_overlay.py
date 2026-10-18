"""
Bounding Box Guide Overlay - Visual movable/resizable OCR capture guide.

Shows a translucent glowing glass frame indicating the active OCR region.
Can be dragged and resized directly over the game window.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizeGrip
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class BBoxOverlay(QWidget):
    """Movable, resizable visual frame showing the OCR capture area."""

    bbox_changed = pyqtSignal(dict)  # {'left': int, 'top': int, 'width': int, 'height': int}

    def __init__(
        self,
        config_manager=None,
        bbox_key: str = "input_bbox",
        title: str = "Input Bar (F4)",
        accent_color: str = "#3b82f6",
        parent=None,
    ):
        super().__init__(parent)
        self._config = config_manager
        self._bbox_key = bbox_key
        self._title = title
        self._accent_color = QColor(accent_color)
        self._drag_position: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._setup_ui()
        self.reload_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Header bar
        self._header = QLabel(f" {self._title} ")
        self._header.setStyleSheet(
            f"background-color: {self._accent_color.name()};"
            "color: white;"
            "font-size: 8pt;"
            "font-weight: bold;"
            "border-radius: 4px;"
            "padding: 2px 6px;"
        )
        self._header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._header, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()

        # Bottom row with size grip
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self._size_grip = QSizeGrip(self)
        self._size_grip.setStyleSheet("background-color: rgba(255, 255, 255, 0.25); border-radius: 3px;")
        bottom_row.addWidget(self._size_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        layout.addLayout(bottom_row)

    def set_accent_color(self, color: str):
        """Update border and header accent color dynamically."""
        self._accent_color = QColor(color)
        self._header.setStyleSheet(
            f"background-color: {self._accent_color.name()};"
            "color: white;"
            "font-size: 8pt;"
            "font-weight: bold;"
            "border-radius: 4px;"
            "padding: 2px 6px;"
        )
        self.update()

    def reload_config(self):
        """Read bbox from config and update geometry."""
        default_bbox = (
            {"left": 265, "top": 350, "width": 645, "height": 45}
            if self._bbox_key == "input_bbox"
            else {"left": 265, "top": 200, "width": 645, "height": 140}
        )
        if self._config:
            cfg = self._config.config if hasattr(self._config, "config") else {}
            cfg_bbox = cfg.get(self._bbox_key)
            if not cfg_bbox and self._bbox_key == "input_bbox":
                cfg_bbox = cfg.get("bbox") or cfg.get("ocr_bbox")
            if cfg_bbox and isinstance(cfg_bbox, dict):
                default_bbox.update(cfg_bbox)

        left = int(default_bbox.get("left", 265))
        top = int(default_bbox.get("top", 350))
        width = max(100, int(default_bbox.get("width", 645)))
        height = max(35, int(default_bbox.get("height", 45)))

        self.setGeometry(left, top, width, height)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_position and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_position
            self.move(new_pos)
            self._notify_change()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        self._notify_change()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._notify_change()

    def _notify_change(self):
        geom = self.geometry()
        bbox = {
            "left": int(geom.x()),
            "top": int(geom.y()),
            "width": int(geom.width()),
            "height": int(geom.height()),
        }
        if self._config:
            self._config.set(self._bbox_key, bbox, auto_save=True)
            if self._bbox_key == "input_bbox":
                self._config.set("bbox", bbox, auto_save=False)
                self._config.set("ocr_bbox", bbox, auto_save=True)
        self.bbox_changed.emit(bbox)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)

        # Translucent glass fill with accent tint
        fill_color = QColor(self._accent_color)
        fill_color.setAlpha(20)
        painter.setBrush(fill_color)

        # Glowing border with accent color
        pen = QPen(self._accent_color, 2)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 8, 8)

        # Subtle inner grid dots for positioning
        pen_dots = QPen(QColor(255, 255, 255, 45), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen_dots)
        painter.drawLine(rect.left() + 20, rect.center().y(), rect.right() - 20, rect.center().y())
