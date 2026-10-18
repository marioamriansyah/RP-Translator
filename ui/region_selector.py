"""
Region Selector - Interactive Fullscreen Screen Snip Tool for OCR.

Allows the user to click and drag to visually select the GTA RP chatbox
or any screen region for OCR capture.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont


class RegionSelector(QWidget):
    """Fullscreen transparent window for drag-to-select screen area."""

    region_selected = pyqtSignal(dict)  # {'left': int, 'top': int, 'width': int, 'height': int}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._start_pos: QPoint | None = None
        self._current_pos: QPoint | None = None
        self._is_selecting = False

    def start_selection(self):
        """Cover all screens and show selector."""
        # Span across all available screen geometry
        total_rect = QRect()
        for screen in QApplication.screens():
            total_rect = total_rect.united(screen.geometry())

        self.setGeometry(total_rect)
        self._start_pos = None
        self._current_pos = None
        self._is_selecting = False
        self.show()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self._is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._is_selecting:
            self._current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            rect = self._get_normalized_rect()

            if rect.width() > 10 and rect.height() > 10:
                # Convert to global desktop coordinates
                global_top_left = self.mapToGlobal(rect.topLeft())
                bbox = {
                    "left": int(global_top_left.x()),
                    "top": int(global_top_left.y()),
                    "width": int(rect.width()),
                    "height": int(rect.height()),
                }
                self.region_selected.emit(bbox)

            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def _get_normalized_rect(self) -> QRect:
        if not self._start_pos or not self._current_pos:
            return QRect()

        x1 = min(self._start_pos.x(), self._current_pos.x())
        y1 = min(self._start_pos.y(), self._current_pos.y())
        x2 = max(self._start_pos.x(), self._current_pos.x())
        y2 = max(self._start_pos.y(), self._current_pos.y())
        return QRect(x1, y1, x2 - x1, y2 - y1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Dark translucent backdrop
        painter.fillRect(self.rect(), QColor(10, 12, 18, 140))

        if self._start_pos and self._current_pos:
            rect = self._get_normalized_rect()

            # 2. Clear out the selected area (reveal desktop behind)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # 3. Apple Cyan glowing glass border
            pen = QPen(QColor(10, 132, 255, 240), 2)
            painter.setPen(pen)
            painter.setBrush(QColor(10, 132, 255, 25))
            painter.drawRoundedRect(rect, 4, 4)

            # Corner handles
            painter.setBrush(QColor(255, 255, 255, 255))
            painter.setPen(Qt.PenStyle.NoPen)
            size = 6
            painter.drawRect(rect.left() - size // 2, rect.top() - size // 2, size, size)
            painter.drawRect(rect.right() - size // 2, rect.top() - size // 2, size, size)
            painter.drawRect(rect.left() - size // 2, rect.bottom() - size // 2, size, size)
            painter.drawRect(rect.right() - size // 2, rect.bottom() - size // 2, size, size)

            # Dimension badge
            text = f" {rect.width()} × {rect.height()} px "
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            painter.setFont(font)

            badge_y = rect.top() - 24 if rect.top() > 30 else rect.bottom() + 8
            badge_rect = QRect(rect.left(), badge_y, 110, 20)

            painter.setBrush(QColor(15, 17, 26, 220))
            painter.setPen(QColor(10, 132, 255, 180))
            painter.drawRoundedRect(badge_rect, 4, 4)

            painter.setPen(QColor(255, 255, 255, 240))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)
        else:
            # Instructions hint at the center
            msg = "Click and drag over your game chatbox to set OCR Area\nPress ESC to cancel"
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)
