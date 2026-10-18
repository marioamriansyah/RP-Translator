"""
PRORP Translator - RP+ Illustrator Edition.

Pixel-perfect implementation of the official Illustrator UI/UX design:
- Geometric Hexagon + RP+ Brand Logo
- Capsule Toolbar: Guide (Active toggle), Snip Input, Snip Chat, Setting
- Recessed Input Box with embedded Style Selector & Circular Action Button
- 3 Dedicated Horizontal Option Cards with Large Accent Numbers (01, 02, 03),
  Vertical dividers, and 1-Click Copy
- Simple, rock-solid Accent Theme customization
"""

from __future__ import annotations

import os
from typing import Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QFrame, QComboBox,
    QSystemTrayIcon, QMenu, QApplication, QSizePolicy,
    QGraphicsOpacityEffect,
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPointF, QPropertyAnimation,
    QEasingCurve,
)
from PyQt6.QtGui import (
    QIcon, QAction, QFont, QPixmap, QPainter, QColor, QPen,
    QBrush, QLinearGradient
)

from ui.settings_dialog import SettingsDialog
from ui.region_selector import RegionSelector
from ui.bbox_overlay import BBoxOverlay
from ui.vector_icons import get_vector_icon, get_app_qicon, create_app_icon, create_rp_plus_logo
from ui.theme_manager import ThemeManager, AccentTheme, PRESET_THEMES, _is_light_color


class RPAnswerCard(QFrame):
    """
    Illustrator-styled Horizontal Translation Card:
    - Left column: Large Accent Number (01, 02, 03) + 'OPSI' label
    - Vertical Divider Line
    - Middle column: Title (Natural, Street, Flavor) + Translation Body
    - Right column: Hotkey Tag (CTRL + 1/2/3) + Copy Button
    """

    copy_requested = pyqtSignal(int)

    def __init__(
        self,
        index: int,
        number_str: str,
        title_str: str,
        accent_color: str,
        hotkey_tag: str,
        parent=None,
    ):
        super().__init__(parent)
        self._index = index
        self._number_str = number_str
        self._title_str = title_str
        self._accent_color = accent_color
        self._raw_text = ""

        self.setObjectName("cardFrame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(94)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)

        # ── 1. Left Block: Number & 'OPSI' ─────────────────────────────
        left_box = QVBoxLayout()
        left_box.setContentsMargins(0, 0, 0, 0)
        left_box.setSpacing(2)
        left_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._num_label = QLabel(number_str)
        self._num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._num_label.setStyleSheet(
            f"font-size: 22pt; font-weight: 800; color: {accent_color}; "
            "font-family: 'Segoe UI', -apple-system, sans-serif; "
            "padding: 0; margin: 0; border: none;"
        )
        left_box.addWidget(self._num_label)

        opsi_label = QLabel("OPSI")
        opsi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        opsi_label.setStyleSheet(
            "font-size: 7.5pt; font-weight: 700; color: #727580; letter-spacing: 1.5px; "
            "padding: 0; margin: 0; border: none;"
        )
        left_box.addWidget(opsi_label)

        left_widget = QWidget()
        left_widget.setFixedWidth(66)
        left_widget.setLayout(left_box)
        layout.addWidget(left_widget)

        # ── 2. Vertical Divider Line ───────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background-color: #2D2F34; width: 1px; max-width: 1px; border: none;")
        sep.setMinimumHeight(50)
        layout.addWidget(sep)

        # ── 3. Middle Block: Title & Translation ───────────────────────
        mid_box = QVBoxLayout()
        mid_box.setSpacing(4)
        mid_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._title_label = QLabel(title_str)
        self._title_label.setStyleSheet(
            "font-size: 12.5pt; font-weight: 700; color: #FFFFFF; font-family: 'Segoe UI', -apple-system, sans-serif;"
        )
        mid_box.addWidget(self._title_label)

        self._text_label = QLabel("Waiting for translation...")
        self._text_label.setWordWrap(True)
        self._text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._text_label.setStyleSheet(
            "font-size: 9.5pt; color: #6D707B;"
        )
        mid_box.addWidget(self._text_label)

        layout.addLayout(mid_box, stretch=1)

        # ── 4. Right Block: Hotkey Tag & Copy Button ───────────────────
        right_box = QHBoxLayout()
        right_box.setSpacing(10)
        right_box.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self._hk_label = QLabel(hotkey_tag)
        self._hk_label.setStyleSheet(
            "font-family: 'Consolas', 'Segoe UI Mono', monospace; "
            "color: #8C8F9A; font-size: 8.5pt; font-weight: 600; padding-right: 2px;"
        )
        right_box.addWidget(self._hk_label)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("cardCopyBtn")
        self._copy_btn.setIcon(get_vector_icon("copy", color="#FFFFFF", size=13))
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        right_box.addWidget(self._copy_btn)

        layout.addLayout(right_box)

    def fade_in(self, delay_ms: int = 0):
        """Smooth cascade fade-in animation when new translation arrives."""
        if not hasattr(self, "_opacity_effect") or self._opacity_effect is None:
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)

        self._opacity_effect.setOpacity(0.15)
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(220)
        self._fade_anim.setStartValue(0.15)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        if delay_ms > 0:
            QTimer.singleShot(delay_ms, self._fade_anim.start)
        else:
            self._fade_anim.start()

    def set_accent_color(self, color: str):
        self._accent_color = color
        self._num_label.setStyleSheet(
            f"font-size: 22pt; font-weight: 800; color: {color}; "
            "font-family: 'Segoe UI', -apple-system, sans-serif; "
            "padding: 0; margin: 0; border: none;"
        )

    def set_text(self, text: str):
        self._raw_text = text.strip() if text else ""
        if self._raw_text:
            self._text_label.setText(self._raw_text)
            self._text_label.setStyleSheet(
                "font-size: 10pt; font-weight: 400; color: #D0D3DC;"
            )
        else:
            self._text_label.setText("Waiting for translation...")
            self._text_label.setStyleSheet(
                "font-size: 9.5pt; color: #6D707B;"
            )

    def get_text(self) -> str:
        return self._raw_text

    def _on_copy_clicked(self):
        self.copy_requested.emit(self._index)
        self._trigger_copy_feedback()

    def _trigger_copy_feedback(self):
        self._copy_btn.setText("Copied!")
        self._copy_btn.setIcon(get_vector_icon("check", color="#FFFFFF", size=13))
        self._copy_btn.setStyleSheet(
            f"background-color: {self._accent_color}; color: #FFFFFF; font-weight: 700; border-radius: 8px;"
        )
        self.setStyleSheet(
            f"QFrame#cardFrame {{ background-color: #242528; border: 1.5px solid {self._accent_color}; border-radius: 16px; }}"
        )
        QTimer.singleShot(1100, self._reset_copy_feedback)

    def _reset_copy_feedback(self):
        self._copy_btn.setText("Copy")
        self._copy_btn.setIcon(get_vector_icon("copy", color="#FFFFFF", size=13))
        self._copy_btn.setStyleSheet("")
        self.setStyleSheet("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._raw_text:
            self.copy_requested.emit(self._index)
            self._trigger_copy_feedback()
        super().mousePressEvent(event)


# Aliases for backward compatibility
LinearAnswerCard = RPAnswerCard
MonochromeAnswerCard = RPAnswerCard


class MainWindow(QMainWindow):
    """
    Main Window for PRORP Translator matching user's Illustrator RP+ design.
    """

    translate_requested = pyqtSignal(str)
    style_changed = pyqtSignal(str)
    copy_answer = pyqtSignal(int)
    settings_requested = pyqtSignal()
    theme_settings_requested = pyqtSignal()
    position_osd_requested = pyqtSignal()

    def __init__(self, config_manager=None, style_manager=None, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._style_manager = style_manager

        # Initialize Theme Manager
        self._theme_manager = ThemeManager.get_instance(self._config)
        self._current_style = "LA Street"

        self.setWindowTitle("RP+ Translator")
        self.resize(680, 740)
        self.setMinimumSize(640, 680)
        self.setStyleSheet(self._theme_manager.get_main_window_qss())
        self.setWindowIcon(get_app_qicon())

        # Sub-tools
        self._snip_target = "input"
        self._region_selector = RegionSelector()
        self._region_selector.region_selected.connect(self._on_region_selected)

        self._bbox_input_overlay = BBoxOverlay(
            config_manager=self._config,
            bbox_key="input_bbox",
            title="Input Bar (F4)",
            accent_color=self._theme_manager.accent_1,
        )
        self._bbox_chatlog_overlay = BBoxOverlay(
            config_manager=self._config,
            bbox_key="chatlog_bbox",
            title="Chatlog History (F3)",
            accent_color=self._theme_manager.accent_2,
        )
        self._bbox_overlay = self._bbox_input_overlay

        self._setup_ui()
        self._setup_tray()
        self._load_styles()

        # Connect internal theme requested & theme change listener
        self.theme_settings_requested.connect(self._open_theme_settings)
        self._theme_manager.theme_changed.connect(self.apply_theme)

        show_bbox = False
        if self._config:
            show_bbox = self._config.get("show_bbox_overlay", False) or self._config.get("show_ocr_bbox", False)
        if show_bbox:
            self._bbox_input_overlay.show()
            self._bbox_chatlog_overlay.show()
            self._guide_btn.setProperty("active", "true")
            self._guide_btn.setStyle(self._guide_btn.style())

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(22, 18, 22, 16)
        main_layout.setSpacing(12)

        # ── 1. Top Header Bar: Logo + Pill Toolbar ─────────────────────
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 2)
        top_bar.setSpacing(12)

        # RP+ Hexagon Brand Logo (User provided asset)
        self._logo_label = QLabel()
        logo_pix = create_rp_plus_logo(scale=1.0, height=28)
        self._logo_label.setPixmap(logo_pix)
        self._logo_label.setFixedSize(logo_pix.width(), logo_pix.height())
        top_bar.addWidget(self._logo_label)

        top_bar.addStretch()

        # Capsule Pill Toolbar
        top_pill = QFrame()
        top_pill.setObjectName("pillToolbar")
        top_pill_layout = QHBoxLayout(top_pill)
        top_pill_layout.setContentsMargins(4, 3, 4, 3)
        top_pill_layout.setSpacing(4)

        # Guide Button (active state = light capsule)
        self._guide_btn = QPushButton("Guide")
        self._guide_btn.setObjectName("toolbarBtn")
        self._guide_btn.setIcon(get_vector_icon("guide", color="#FFFFFF", size=15))
        self._guide_btn.setToolTip("Show / hide visual capture guide frames on screen")
        self._guide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._guide_btn.clicked.connect(self._toggle_bbox_overlay)
        top_pill_layout.addWidget(self._guide_btn)

        # Snip Input Button
        self._snip_input_btn = QPushButton("Snip Input")
        self._snip_input_btn.setObjectName("toolbarBtn")
        self._snip_input_btn.setIcon(get_vector_icon("snip_input", color="#FFFFFF", size=15))
        self._snip_input_btn.setToolTip("Set screen area where you type in-game (F4)")
        self._snip_input_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._snip_input_btn.clicked.connect(self._start_snip_input)
        top_pill_layout.addWidget(self._snip_input_btn)

        # Snip Chat Button
        self._snip_chat_btn = QPushButton("Snip Chat")
        self._snip_chat_btn.setObjectName("toolbarBtn")
        self._snip_chat_btn.setIcon(get_vector_icon("snip_chat", color="#FFFFFF", size=15))
        self._snip_chat_btn.setToolTip("Set screen area for incoming chat history (F3)")
        self._snip_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._snip_chat_btn.clicked.connect(self._start_snip_chatlog)
        top_pill_layout.addWidget(self._snip_chat_btn)

        # Setting Button
        self._settings_btn = QPushButton("Setting")
        self._settings_btn.setObjectName("toolbarBtn")
        self._settings_btn.setIcon(get_vector_icon("setting", color="#FFFFFF", size=15))
        self._settings_btn.setToolTip("Open Settings & Theme dialog")
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.clicked.connect(self.settings_requested.emit)
        top_pill_layout.addWidget(self._settings_btn)

        top_bar.addWidget(top_pill)
        main_layout.addLayout(top_bar)

        # ── 2. Sub-Header: Roleplay Dialect & Guide Description ────────
        sub_hdr = QHBoxLayout()
        sub_title = QLabel("ROLEPLAY DIALECT / STYLE")
        sub_title.setStyleSheet("font-size: 7.5pt; font-weight: 600; color: #6D707B; letter-spacing: 0.8px;")
        sub_hdr.addWidget(sub_title)

        sub_hdr.addStretch()

        self._sub_desc_lbl = QLabel("Select the screen area (region) you wish to translate.")
        self._sub_desc_lbl.setStyleSheet("font-size: 8pt; color: #6D707B;")
        sub_hdr.addWidget(self._sub_desc_lbl)
        main_layout.addLayout(sub_hdr)

        # ── 3. Indonesia Source ( Chat Input ) Card ────────────────────
        input_card = QFrame()
        input_card.setObjectName("cardFrame")
        input_card_layout = QVBoxLayout(input_card)
        input_card_layout.setContentsMargins(18, 14, 18, 14)
        input_card_layout.setSpacing(10)

        # Input Card Header
        input_hdr = QHBoxLayout()
        input_hdr_lbl = QLabel("Indonesia Source ( Chat Input )")
        input_hdr_lbl.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #8C8F9A;")
        input_hdr.addWidget(input_hdr_lbl)

        input_hdr.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("clearPillBtn")
        clear_btn.setIcon(get_vector_icon("clear", color="#FFFFFF", size=10))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_input)
        input_hdr.addWidget(clear_btn)

        input_card_layout.addLayout(input_hdr)

        # Recessed Text Input + Style Dropdown + Circular Translate Button
        input_box = QFrame()
        input_box.setObjectName("inputFieldBox")
        input_box_layout = QHBoxLayout(input_box)
        input_box_layout.setContentsMargins(10, 4, 6, 4)
        input_box_layout.setSpacing(8)

        self._input_text = QTextEdit()
        self._input_text.setObjectName("inputEdit")
        self._input_text.setPlaceholderText("Typing your word at here")
        self._input_text.setFixedHeight(48)
        input_box_layout.addWidget(self._input_text, stretch=1)

        # Embedded Style Selector Dropdown
        self._style_combo = QComboBox()
        self._style_combo.setObjectName("styleSelectorCombo")
        self._style_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_combo.currentTextChanged.connect(self._on_style_combo_changed)
        input_box_layout.addWidget(self._style_combo)

        # Circular Action Button (Translate)
        self._translate_btn = QPushButton()
        self._translate_btn.setObjectName("circleTranslateBtn")
        self._translate_btn.setIcon(get_vector_icon("chevron_right", color="#141517", size=16))
        self._translate_btn.setToolTip("Translate (Enter / F4)")
        self._translate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._translate_btn.clicked.connect(self._on_translate)
        input_box_layout.addWidget(self._translate_btn)

        input_card_layout.addWidget(input_box)
        main_layout.addWidget(input_card)

        # ── 4. Translation Options Label ───────────────────────────────
        ans_hdr = QHBoxLayout()
        ans_title = QLabel("Translation Options (Click Any Card or Press Hotkey to Copy)")
        ans_title.setStyleSheet("font-size: 7.5pt; font-weight: 600; color: #6D707B; letter-spacing: 0.5px; margin-top: 2px;")
        ans_hdr.addWidget(ans_title)
        ans_hdr.addStretch()
        main_layout.addLayout(ans_hdr)

        # ── 5. Three Dedicated Horizontal Option Cards ─────────────────
        self._cards: list[RPAnswerCard] = []
        tm = self._theme_manager

        card_configs = [
            (0, "01", "Natural", tm.accent_1, "CTRL + 1"),
            (1, "02", "Street", tm.accent_2, "CTRL + 2"),
            (2, "03", "Flavor", tm.accent_3, "CTRL + 3"),
        ]

        for idx, num, title, col, hk in card_configs:
            card = RPAnswerCard(idx, num, title, col, hk)
            card.copy_requested.connect(self.copy_answer.emit)
            self._cards.append(card)
            main_layout.addWidget(card)

        main_layout.addStretch()

        # ── 6. Bottom Footer ───────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("footerFrame")
        footer.setFixedHeight(28)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(4, 0, 4, 0)
        footer_layout.setSpacing(8)

        # Left status
        self._live_dot = QLabel("●")
        self._live_dot.setStyleSheet("color: #30D158; font-size: 7.5pt;")
        footer_layout.addWidget(self._live_dot)

        self._footer_style_lbl = QLabel(self._current_style)
        self._footer_style_lbl.setStyleSheet("color: #FFFFFF; font-size: 8.5pt; font-weight: 600;")
        footer_layout.addWidget(self._footer_style_lbl)

        sep_lbl = QLabel("|")
        sep_lbl.setStyleSheet("color: #44474F; font-size: 8.5pt;")
        footer_layout.addWidget(sep_lbl)

        self._status_lbl = QLabel("Connected")
        self._status_lbl.setStyleSheet("color: #8A8D98; font-size: 8.5pt;")
        footer_layout.addWidget(self._status_lbl)

        footer_layout.addStretch()

        # Right copyright
        copy_lbl = QLabel("RP Plus 1.0.1  •  © Copyrights 2026")
        copy_lbl.setStyleSheet("color: #555862; font-size: 8pt;")
        footer_layout.addWidget(copy_lbl)

        main_layout.addWidget(footer)
        self.setCentralWidget(central)

    # ── Style Management ───────────────────────────────────────────────

    def _load_styles(self):
        """Populate style combo box."""
        self._style_combo.blockSignals(True)
        self._style_combo.clear()

        style_names = ["LA Street", "Cartel Mexico", "Mafia Italy", "American Formal", "British Formal"]
        if self._style_manager:
            custom_styles = self._style_manager.get_style_names()
            for s in custom_styles:
                if s not in style_names:
                    style_names.append(s)

        for s in style_names:
            self._style_combo.addItem(s)

        saved = "LA Street"
        if self._config:
            saved = self._config.get("last_style") or self._config.get("current_style") or "LA Street"

        idx = self._style_combo.findText(saved)
        if idx >= 0:
            self._style_combo.setCurrentIndex(idx)
            self._current_style = saved
        else:
            self._current_style = style_names[0]

        self._style_combo.blockSignals(False)
        self._footer_style_lbl.setText(self._current_style)

    def _on_style_combo_changed(self, name: str):
        if not name:
            return
        self._current_style = name
        self._footer_style_lbl.setText(name)
        if self._config:
            self._config.set("last_style", name, auto_save=False)
            self._config.set("current_style", name, auto_save=True)
        self.style_changed.emit(name)

    def refresh_styles(self):
        self._load_styles()

    def get_selected_style(self) -> str:
        return self._current_style

    # ── Theme Customization ───────────────────────────────────────────

    def apply_theme(self, theme: AccentTheme):
        """Update answer card accent numbers and overlays."""
        if len(self._cards) >= 3:
            self._cards[0].set_accent_color(theme.accent_1)
            self._cards[1].set_accent_color(theme.accent_2)
            self._cards[2].set_accent_color(theme.accent_3)

        self._bbox_input_overlay.set_accent_color(theme.accent_1)
        self._bbox_chatlog_overlay.set_accent_color(theme.accent_2)

    def _open_theme_settings(self):
        self.open_settings(initial_tab=0)

    # ── Public API (Backward Compatibility with app.py) ───────────────

    def set_answers(self, ans1: str, ans2: str, ans3: str):
        texts = [ans1, ans2, ans3]
        for i, card in enumerate(self._cards):
            card.set_text(texts[i])
            # Smooth staggered cascade entrance animation
            card.fade_in(delay_ms=i * 65)

    def get_answer(self, index: int) -> str:
        if 0 <= index < len(self._cards):
            return self._cards[index].get_text()
        return ""

    def set_input_text(self, text: str):
        self._input_text.setPlainText(text)

    def get_input_text(self) -> str:
        return self._input_text.toPlainText().strip()

    def set_status(self, message: str):
        self._status_lbl.setText(message)

    def set_translating(self, translating: bool):
        self._translate_btn.setEnabled(not translating)
        if translating:
            self._status_lbl.setText("Translating...")
            self._live_dot.setStyleSheet("color: #F59E0B; font-size: 7.5pt;")
            self._start_translating_pulse()
        else:
            self._status_lbl.setText("Connected")
            self._live_dot.setStyleSheet("color: #30D158; font-size: 7.5pt;")
            self._stop_translating_pulse()

    def _start_translating_pulse(self):
        """Pulsing breathing animation on the circular translate button during translation."""
        if not hasattr(self, "_btn_opacity") or self._btn_opacity is None:
            self._btn_opacity = QGraphicsOpacityEffect(self._translate_btn)
            self._translate_btn.setGraphicsEffect(self._btn_opacity)
        self._btn_anim = QPropertyAnimation(self._btn_opacity, b"opacity")
        self._btn_anim.setDuration(450)
        self._btn_anim.setStartValue(1.0)
        self._btn_anim.setEndValue(0.3)
        self._btn_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._btn_anim.setLoopCount(-1)
        self._btn_anim.start()

    def _stop_translating_pulse(self):
        """Stops the pulse animation and restores button to full opacity."""
        if hasattr(self, "_btn_anim") and self._btn_anim:
            self._btn_anim.stop()
        if hasattr(self, "_btn_opacity") and self._btn_opacity:
            self._btn_opacity.setOpacity(1.0)

    def _clear_input(self):
        self._input_text.clear()
        # Micro animation on input box: brief subtle flash
        if not hasattr(self, "_input_opacity") or self._input_opacity is None:
            self._input_opacity = QGraphicsOpacityEffect(self._input_text)
            self._input_text.setGraphicsEffect(self._input_opacity)
        self._input_anim = QPropertyAnimation(self._input_opacity, b"opacity")
        self._input_anim.setDuration(160)
        self._input_anim.setStartValue(0.4)
        self._input_anim.setEndValue(1.0)
        self._input_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._input_anim.start()

    def _on_translate(self):
        text = self._input_text.toPlainText().strip()
        if text:
            self.translate_requested.emit(text)

    # ── Snip & BBox Actions ───────────────────────────────────────────

    def _start_snip_input(self):
        self._snip_target = "input"
        self._sub_desc_lbl.setText("Drag crosshairs over where you TYPE in-game (T)...")
        self._region_selector.start_selection()

    def _start_snip_chatlog(self):
        self._snip_target = "chatlog"
        self._sub_desc_lbl.setText("Drag crosshairs over incoming CHATLOG history...")
        self._region_selector.start_selection()

    def _start_snip(self):
        self._start_snip_input()

    def _on_region_selected(self, bbox: dict):
        if self._snip_target == "input":
            if self._config:
                self._config.set("input_bbox", bbox, auto_save=False)
                self._config.set("bbox", bbox, auto_save=False)
                self._config.set("ocr_bbox", bbox, auto_save=True)
            self._bbox_input_overlay.reload_config()
            self._bbox_input_overlay.show()
            self._sub_desc_lbl.setText(f"Input Bar set: {bbox['width']}x{bbox['height']} at ({bbox['left']}, {bbox['top']})")
        else:
            if self._config:
                self._config.set("chatlog_bbox", bbox, auto_save=True)
            self._bbox_chatlog_overlay.reload_config()
            self._bbox_chatlog_overlay.show()
            self._sub_desc_lbl.setText(f"Chatlog set: {bbox['width']}x{bbox['height']} at ({bbox['left']}, {bbox['top']})")

    def _toggle_bbox_overlay(self):
        if self._bbox_input_overlay.isVisible() or self._bbox_chatlog_overlay.isVisible():
            self._bbox_input_overlay.hide()
            self._bbox_chatlog_overlay.hide()
            self._guide_btn.setProperty("active", "false")
            self._guide_btn.setIcon(get_vector_icon("guide", color="#FFFFFF", size=15))
            self._guide_btn.setStyle(self._guide_btn.style())
            if self._config:
                self._config.set("show_bbox_overlay", False)
        else:
            self._bbox_input_overlay.reload_config()
            self._bbox_input_overlay.show()
            self._bbox_chatlog_overlay.reload_config()
            self._bbox_chatlog_overlay.show()
            self._guide_btn.setProperty("active", "true")
            self._guide_btn.setIcon(get_vector_icon("guide", color="#141517", size=15))
            self._guide_btn.setStyle(self._guide_btn.style())
            if self._config:
                self._config.set("show_bbox_overlay", True)

    # ── Tray & Window Lifecycle ───────────────────────────────────────

    def _setup_tray(self):
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(get_app_qicon())
        self._tray_icon.setToolTip("RP+ Translator")

        self._tray_menu = QMenu()
        self._tray_menu.setStyleSheet(
            "QMenu { background-color: #1E1F21; color: #FFFFFF; "
            "border: 1px solid #28292C; border-radius: 8px; padding: 4px; }"
            "QMenu::item { padding: 6px 16px; border-radius: 4px; }"
            "QMenu::item:selected { background-color: #2D2F34; color: #FFFFFF; }"
        )

        show_act = QAction("Show / Hide Window", self)
        show_act.triggered.connect(self.toggle_visibility)
        self._tray_menu.addAction(show_act)

        theme_act = QAction("Customize Accent Theme", self)
        theme_act.triggered.connect(self._open_theme_settings)
        self._tray_menu.addAction(theme_act)

        snip_act = QAction("Snip OCR Region", self)
        snip_act.triggered.connect(self._start_snip)
        self._tray_menu.addAction(snip_act)

        self._tray_menu.addSeparator()

        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self._quit_app)
        self._tray_menu.addAction(quit_act)

        self._tray_icon.setContextMenu(self._tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visibility()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        if self._tray_icon and self._tray_icon.isVisible():
            event.ignore()
            self.hide()
        else:
            event.accept()

    def _quit_app(self):
        if self._bbox_overlay:
            self._bbox_overlay.close()
        if self._tray_icon:
            self._tray_icon.hide()
        QApplication.instance().quit()

    def open_settings(self, config_manager=None, style_manager=None, initial_tab: int = 0):
        dlg = SettingsDialog(
            config_manager=config_manager or self._config,
            style_manager=style_manager or self._style_manager,
            initial_tab=initial_tab,
            parent=self,
        )
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            settings = dlg.get_settings()
            if self._config:
                if "theme" in settings:
                    tm = ThemeManager.get_instance(self._config)
                    self.apply_theme(tm.current_theme)
            return settings
        return None
