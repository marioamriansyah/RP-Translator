"""
OSD Overlay - Apple Liquid Glass On-Screen Display for PRORP Translator.

Frameless, always-on-top, click-through liquid glass overlay window
that renders translation results floating seamlessly over the game.
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QGuiApplication


class OSDOverlay(QWidget):
    """Liquid glass on-screen display overlay for showing translations."""

    scroll_up_requested = pyqtSignal()
    scroll_down_requested = pyqtSignal()

    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._scroll_offset = 0
        self._lines = []
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide)

        self._setup_window_flags()
        self._setup_ui()
        self._apply_config()

        self.scroll_up_requested.connect(self._scroll_up)
        self.scroll_down_requested.connect(self._scroll_down)

    def _setup_window_flags(self):
        """Configure window to be frameless, always-on-top, draggable and resizable liquid glass overlay."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self._drag_pos = None
        self._resize_mode = 0
        self._press_pos = None
        self._press_geometry = None
        self.BORDER_MARGIN = 10

    def _get_resize_mode(self, pos: QPoint) -> int:
        """Determine resize direction based on cursor proximity to borders."""
        mode = 0
        w = self.width()
        h = self.height()
        m = getattr(self, "BORDER_MARGIN", 10)

        if pos.x() <= m:
            mode |= 1  # LEFT
        elif pos.x() >= w - m:
            mode |= 2  # RIGHT

        if pos.y() <= m:
            mode |= 4  # TOP
        elif pos.y() >= h - m:
            mode |= 8  # BOTTOM

        return mode

    def _update_cursor_for_mode(self, mode: int):
        """Update mouse cursor shape depending on resize edge."""
        if mode in (1 | 4, 2 | 8):  # TOP-LEFT or BOTTOM-RIGHT
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif mode in (2 | 4, 1 | 8):  # TOP-RIGHT or BOTTOM-LEFT
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif mode in (1, 2):  # LEFT or RIGHT
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif mode in (4, 8):  # TOP or BOTTOM
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def _setup_ui(self):
        """Build the overlay UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 12)

        self._label = QLabel("")
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._label.setCursor(Qt.CursorShape.SizeAllCursor)

        layout.addWidget(self._label)
        self.setLayout(layout)

    def _apply_config(self):
        """Apply settings from config manager."""
        if self._config:
            cfg = self._config.config if hasattr(self._config, "config") else {}
        else:
            cfg = {}

        osd_bbox = cfg.get("osd_bbox", {})
        left = int(osd_bbox.get("left", 11))
        top = int(osd_bbox.get("top", 620))
        width = max(150, int(osd_bbox.get("width", 671)))
        height = max(80, int(osd_bbox.get("height", 220)))

        # Fallback calculation: Directly below input bar
        input_bbox = cfg.get("input_bbox", {})
        in_left = int(input_bbox.get("left", 11))
        in_top = int(input_bbox.get("top", 557))
        in_h = int(input_bbox.get("height", 53))
        default_top = in_top + in_h + 10
        default_width = max(150, int(input_bbox.get("width", 671)))

        # Sanity check: Ensure OSD is positioned on a connected visible monitor.
        # If coordinates are off-screen (e.g. secondary monitor disconnected or negative coordinate on single screen),
        # automatically fallback to directly below the input bar on the primary monitor.
        screens = QGuiApplication.screens()
        is_visible = False
        target_rect = QRect(left, top, width, height)
        for screen in screens:
            geom = screen.geometry()
            if geom.intersects(target_rect):
                intersect = geom.intersected(target_rect)
                if intersect.width() >= 100 and intersect.height() >= 50:
                    is_visible = True
                    break

        if not is_visible:
            left = in_left
            top = default_top
            width = default_width

        self._font_color = cfg.get("osd_font_color", "#F7F8F8")
        self._font_size = cfg.get("osd_font_size", 12)
        self._duration = cfg.get("osd_duration", 12)
        self._enabled = cfg.get("osd_enabled", True)

        try:
            from ui.theme_manager import ThemeManager
            self._theme = ThemeManager.get_instance(self._config).current_theme
            if not cfg.get("osd_font_color"):
                self._font_color = self._theme.text_primary
        except Exception:
            self._theme = None

        self.setGeometry(left, top, width, height)
        self._update_style()

    def apply_theme(self, theme):
        """Apply theme dynamically without restarting."""
        try:
            self._theme = theme
            self._font_color = getattr(theme, "text_primary", "#FFFFFF")
            self._update_style()
            self._render_text()
            self.update()
        except Exception as e:
            print(f"[OSDOverlay] apply_theme warning: {e}")

    def _update_style(self):
        """Update label styling with Linear aesthetic."""
        self._label.setStyleSheet(
            f"QLabel {{"
            f"  color: {self._font_color};"
            f"  font-size: {self._font_size}pt;"
            f"  font-weight: 600;"
            f"  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;"
            f"  background: transparent;"
            f"  line-height: 1.45;"
            f"}}"
        )

    def reload_config(self):
        """Reload configuration (called after settings change)."""
        self._apply_config()

    def show_translation(self, text: str):
        """Display translation text on the overlay."""
        if not self._enabled:
            return

        self._lines = text.split("\n")
        self._scroll_offset = 0
        self._render_text()

        self.show()
        self.raise_()

        if self._duration > 0:
            self._auto_hide_timer.start(self._duration * 1000)

    def _render_text(self):
        """Render visible lines with rich formatted Linear badges."""
        line_height = self._font_size * 2 + 8
        available_height = max(50, self.height() - 28)
        max_visible = max(1, available_height // line_height)

        visible = self._lines[self._scroll_offset: self._scroll_offset + max_visible]

        t = self._theme
        b1 = getattr(t, "accent_1", "#FF453A")
        b2 = getattr(t, "accent_2", "#30D158")
        b3 = getattr(t, "accent_3", "#0A84FF")
        b_base = getattr(t, "border_base", "#28292C")

        from ui.theme_manager import _is_light_color
        fg1 = "#141517" if (t and _is_light_color(b1)) else "#ffffff"
        fg2 = "#141517" if (t and _is_light_color(b2)) else "#ffffff"
        fg3 = "#141517" if (t and _is_light_color(b3)) else "#ffffff"

        # Format with rich HTML badges
        html_lines = []
        for line in visible:
            line = line.strip()
            if not line:
                continue

            badge_bg = b1
            badge_fg = fg1
            if line.startswith("[1]"):
                badge_bg = b1
                badge_fg = fg1
            elif line.startswith("[2]"):
                badge_bg = b2
                badge_fg = fg2
            elif line.startswith("[3]"):
                badge_bg = b3
                badge_fg = fg3
            elif line.startswith("[F1") or "[Arti" in line[:15]:
                badge_bg = b1
                badge_fg = fg1
            elif line.startswith("[Chat") or line.startswith("[F5"):
                badge_bg = b2
                badge_fg = fg2
            elif line.startswith("[Input") or line.startswith("[F4"):
                badge_bg = b3
                badge_fg = fg3
            else:
                badge_bg = b_base
                badge_fg = getattr(t, "text_primary", "#FFFFFF") if t else "#FFFFFF"

            formatted = line
            if line.startswith("[") and "]" in line:
                tag, rest = line.split("]", 1)
                formatted = f"<span style='background-color: {badge_bg}; color: {badge_fg}; padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 8.5pt;'>{tag}]</span> <span style='color: {self._font_color};'>{rest}</span>"
            else:
                formatted = f"<span style='color: {self._font_color};'>{line}</span>"

            html_lines.append(f"<div style='margin-bottom: 6px;'>{formatted}</div>")

        result_html = "".join(html_lines)
        if self._scroll_offset > 0:
            result_html = "<div style='color: #8E8E93; font-size: 8pt;'>▲ More above</div>" + result_html
        if self._scroll_offset + max_visible < len(self._lines):
            result_html = result_html + "<div style='color: #8E8E93; font-size: 8pt;'>▼ More below</div>"

        self._label.setText(result_html)

    def _scroll_up(self):
        if self._scroll_offset > 0:
            self._scroll_offset -= 1
            self._render_text()
            if self._duration > 0 and self._auto_hide_timer.isActive():
                self._auto_hide_timer.start(self._duration * 1000)

    def _scroll_down(self):
        if self._scroll_offset < len(self._lines) - 1:
            self._scroll_offset += 1
            self._render_text()
            if self._duration > 0 and self._auto_hide_timer.isActive():
                self._auto_hide_timer.start(self._duration * 1000)

    def scroll_up(self):
        self.scroll_up_requested.emit()

    def scroll_down(self):
        self.scroll_down_requested.emit()

    def hide_osd(self):
        self._auto_hide_timer.stop()
        self.hide()

    def resizeEvent(self, event):
        """Re-render visible text dynamically when user resizes the OSD."""
        super().resizeEvent(event)
        self._render_text()

    def mousePressEvent(self, event):
        """Begin dragging or resizing the overlay when left-clicked."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            self._resize_mode = self._get_resize_mode(pos)
            self._press_pos = event.globalPosition().toPoint()
            self._press_geometry = self.geometry()
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._auto_hide_timer.stop()
            event.accept()

    def mouseMoveEvent(self, event):
        """Move or resize the overlay window as the cursor moves."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            # Hovering without click: update cursor shape based on edge proximity
            mode = self._get_resize_mode(event.position().toPoint())
            self._update_cursor_for_mode(mode)
            event.accept()
            return

        # Resizing mode
        if self._resize_mode != 0 and self._press_geometry is not None:
            diff = event.globalPosition().toPoint() - self._press_pos
            geo = QRect(self._press_geometry)

            min_w, min_h = 220, 90
            max_w, max_h = 1920, 1080

            # Horizontal resize
            if self._resize_mode & 2:  # RIGHT
                new_w = max(min_w, min(max_w, geo.width() + diff.x()))
                geo.setWidth(new_w)
            elif self._resize_mode & 1:  # LEFT
                new_w = max(min_w, min(max_w, geo.width() - diff.x()))
                geo.setLeft(geo.right() - new_w)

            # Vertical resize
            if self._resize_mode & 8:  # BOTTOM
                new_h = max(min_h, min(max_h, geo.height() + diff.y()))
                geo.setHeight(new_h)
            elif self._resize_mode & 4:  # TOP
                new_h = max(min_h, min(max_h, geo.height() - diff.y()))
                geo.setTop(geo.bottom() - new_h)

            self.setGeometry(geo)
            event.accept()
        elif self._drag_pos is not None:
            # Moving the entire overlay
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Finish dragging/resizing and automatically save position & size to config."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            self._resize_mode = 0
            self._press_geometry = None
            self._press_pos = None

            if self._config:
                osd_bbox = self._config.get("osd_bbox", {})
                if not isinstance(osd_bbox, dict):
                    osd_bbox = {}
                osd_bbox["left"] = int(self.x())
                osd_bbox["top"] = int(self.y())
                osd_bbox["width"] = int(self.width())
                osd_bbox["height"] = int(self.height())
                self._config.set("osd_bbox", osd_bbox, auto_save=True)

            if self._duration > 0:
                self._auto_hide_timer.start(self._duration * 1000)

            mode = self._get_resize_mode(event.position().toPoint())
            self._update_cursor_for_mode(mode)
            event.accept()

    def leaveEvent(self, event):
        """Reset cursor to move-crosshair when mouse leaves overlay."""
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        super().leaveEvent(event)

    def show_preview(self):
        """Show an interactive preview card so user can easily reposition and resize the OSD."""
        preview_text = (
            "[1] In-Game OSD (Tahan untuk Geser • Tarik Tepi/Sudut untuk Ubah Ukuran)\n"
            "[2] Tekan F4 untuk translate apa yang Anda ketik\n"
            "[3] Tekan F3 untuk translate chatlog masuk\n"
            "Posisi dan ukuran otomatis tersimpan saat mouse dilepas."
        )
        self.show_translation(preview_text)

    def paintEvent(self, event):
        """Draw Linear floating HUD frosted background with subtle violet sheen, drag handle, and resize grip."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)

        # 1. Dark background body with alpha
        bg_hex = getattr(self._theme, "bg_primary", "#141517") if self._theme else "#141517"
        bg_col = QColor(bg_hex)
        if not bg_col.isValid():
            bg_col = QColor("#141517")
        bg_col.setAlpha(232)
        painter.setBrush(bg_col)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8)

        # 2. Refined border
        border_hex = getattr(self._theme, "border_base", "#28292C") if self._theme else "#28292C"
        border_col = QColor(border_hex)
        if not border_col.isValid():
            border_col = QColor("#28292C")
        pen = QPen(border_col, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 8, 8)

        # 3. Top subtle accent sheen
        accent_hex = getattr(self._theme, "accent_1", "#FF453A") if self._theme else "#FF453A"
        acc = QColor(accent_hex)
        if not acc.isValid():
            acc = QColor("#FF453A")
        pen_glow = QPen(QColor(acc.red(), acc.green(), acc.blue(), 75), 1.5)
        painter.setPen(pen_glow)
        painter.drawLine(rect.left() + 8, rect.top(), rect.right() - 8, rect.top())

        # 4. Drag handle pill indicator at top center
        painter.setBrush(QColor(255, 255, 255, 45))
        painter.setPen(Qt.PenStyle.NoPen)
        hw = 36
        hx = rect.center().x() - hw // 2
        painter.drawRoundedRect(hx, rect.top() + 5, hw, 3, 1, 1)

        # 5. Bottom-right subtle diagonal resize grip indicator
        grip_pen = QPen(QColor(255, 255, 255, 50), 1.5)
        painter.setPen(grip_pen)
        rx = rect.right() - 4
        ry = rect.bottom() - 4
        painter.drawLine(rx - 3, ry, rx, ry - 3)
        painter.drawLine(rx - 7, ry, rx, ry - 7)
        painter.drawLine(rx - 11, ry, rx, ry - 11)
