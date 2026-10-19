"""
Modern Settings Dialog - Clean pro utility settings for PRORP Translator.

Tabs: Accent Theme, API, Hotkeys, OCR, Overlay (OSD), Styles
No emojis, clean modern styling.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton,
    QListWidget, QColorDialog, QGroupBox, QMessageBox, QGridLayout,
    QComboBox, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QDesktopServices

from ui.style_editor import StyleEditorDialog
from ui.region_selector import RegionSelector
from ui.vector_icons import get_vector_icon, get_app_qicon
from ui.theme_manager import ThemeManager, PRESET_THEMES, AccentTheme


class ThemePresetCard(QFrame):
    """Visual clickable card for preset accent theme selection."""

    preset_selected = pyqtSignal(str)

    def __init__(self, preset_name: str, theme: AccentTheme, parent=None):
        super().__init__(parent)
        self._name = preset_name
        self._theme = theme
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(62)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)

        # Header with title & color dots
        top_row = QHBoxLayout()
        name_lbl = QLabel(preset_name)
        name_lbl.setStyleSheet("font-weight: 700; font-size: 8.5pt; color: #FFFFFF;")
        top_row.addWidget(name_lbl)
        top_row.addStretch()

        for col in [theme.accent_1, theme.accent_2, theme.accent_3]:
            dot = QLabel()
            dot.setFixedSize(11, 11)
            dot.setStyleSheet(
                f"background-color: {col}; border-radius: 5px; border: 1px solid rgba(255,255,255,0.25);"
            )
            top_row.addWidget(dot)
        layout.addLayout(top_row)

        desc_lbl = QLabel(theme.description)
        desc_lbl.setStyleSheet("font-size: 7.5pt; color: #8A8D98;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        self.set_active(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.preset_selected.emit(self._name)
        super().mousePressEvent(event)

    def set_active(self, active: bool, accent_color: str = "#FF453A"):
        if active:
            self.setStyleSheet(
                f"QFrame {{ background-color: rgba(255, 255, 255, 0.08); "
                f"border: 2px solid {accent_color}; border-radius: 8px; }}"
            )
        else:
            self.setStyleSheet(
                "QFrame { background-color: rgba(255, 255, 255, 0.02); "
                "border: 1px solid #28292C; border-radius: 8px; }"
                "QFrame:hover { background-color: rgba(255, 255, 255, 0.05); border-color: #38393E; }"
            )


class SettingsDialog(QDialog):
    """Full settings dialog with clean pro utility aesthetic and accent customizer."""

    settings_applied = pyqtSignal(dict)
    test_ocr_requested = pyqtSignal()

    def __init__(self, config_manager=None, style_manager=None, initial_tab: int = 0, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._style_manager = style_manager
        self._initial_tab = initial_tab

        tm = ThemeManager.get_instance(self._config)
        self._active_preset = tm.current_theme.name
        self._preset_cards: dict[str, ThemePresetCard] = {}

        self.setWindowTitle("Settings")
        self.setWindowIcon(get_app_qicon())
        self.resize(540, 620)
        self.setStyleSheet(tm.get_settings_qss())

        self._snip_mode = "input"
        self._region_selector = RegionSelector()
        self._region_selector.region_selected.connect(self._on_snip_selected)

        self._setup_ui()
        self._load_settings()

        if 0 <= initial_tab < self._tabs.count():
            self._tabs.setCurrentIndex(initial_tab)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_theme_tab(), "Accent Theme")
        self._tabs.addTab(self._create_api_tab(), "API")
        self._tabs.addTab(self._create_hotkeys_tab(), "Hotkeys")
        self._tabs.addTab(self._create_ocr_tab(), "OCR")
        self._tabs.addTab(self._create_osd_tab(), "Overlay (OSD)")
        self._tabs.addTab(self._create_styles_tab(), "Styles")
        layout.addWidget(self._tabs)

        # Bottom buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self._apply_btn = QPushButton("Apply")
        self._apply_btn.clicked.connect(self._on_apply)
        btn_box.addWidget(self._apply_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self._cancel_btn)

        self._ok_btn = QPushButton("Save")
        self._ok_btn.setIcon(get_vector_icon("save", color="#141517", size=14))
        self._ok_btn.setStyleSheet(
            "QPushButton { background-color: #D4D4D8; border: none; color: #141517; font-weight: 700; padding: 6px 22px; border-radius: 9999px; }"
            "QPushButton:hover { background-color: #FFFFFF; }"
        )
        self._ok_btn.clicked.connect(self._on_ok)
        btn_box.addWidget(self._ok_btn)

        layout.addLayout(btn_box)

    # ── 1. Accent Theme Tab ──────────────────────────────

    def _create_theme_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 1. Preset Gallery
        preset_box = QGroupBox("Preset Accent Themes")
        preset_layout = QGridLayout(preset_box)
        preset_layout.setSpacing(8)

        presets = list(PRESET_THEMES.keys())
        for idx, p_name in enumerate(presets):
            theme_obj = PRESET_THEMES[p_name]
            card = ThemePresetCard(p_name, theme_obj)
            card.preset_selected.connect(self._on_preset_clicked)
            row = idx // 2
            col = idx % 2
            preset_layout.addWidget(card, row, col)
            self._preset_cards[p_name] = card

        layout.addWidget(preset_box)

        # 2. Personalize Accent Colors
        custom_group = QGroupBox("Personalize 3-Option Accents")
        custom_form = QFormLayout(custom_group)
        custom_form.setSpacing(10)

        # Option 1 Accent (01 Natural)
        row1 = QHBoxLayout()
        self._accent_1_input = QLineEdit("#FF453A")
        self._accent_1_input.setMaximumWidth(100)
        self._accent_1_input.textChanged.connect(self._on_custom_color_changed)
        row1.addWidget(self._accent_1_input)

        self._accent_1_preview = QLabel()
        self._accent_1_preview.setFixedSize(24, 24)
        row1.addWidget(self._accent_1_preview)

        pick1_btn = QPushButton("Choose Color")
        pick1_btn.clicked.connect(lambda: self._pick_accent_color(1))
        row1.addWidget(pick1_btn)
        row1.addStretch()
        custom_form.addRow("Option 1 Accent (01 Natural):", row1)

        # Option 2 Accent (02 Street)
        row2 = QHBoxLayout()
        self._accent_2_input = QLineEdit("#30D158")
        self._accent_2_input.setMaximumWidth(100)
        self._accent_2_input.textChanged.connect(self._on_custom_color_changed)
        row2.addWidget(self._accent_2_input)

        self._accent_2_preview = QLabel()
        self._accent_2_preview.setFixedSize(24, 24)
        row2.addWidget(self._accent_2_preview)

        pick2_btn = QPushButton("Choose Color")
        pick2_btn.clicked.connect(lambda: self._pick_accent_color(2))
        row2.addWidget(pick2_btn)
        row2.addStretch()
        custom_form.addRow("Option 2 Accent (02 Street):", row2)

        # Option 3 Accent (03 Flavor)
        row3 = QHBoxLayout()
        self._accent_3_input = QLineEdit("#0A84FF")
        self._accent_3_input.setMaximumWidth(100)
        self._accent_3_input.textChanged.connect(self._on_custom_color_changed)
        row3.addWidget(self._accent_3_input)

        self._accent_3_preview = QLabel()
        self._accent_3_preview.setFixedSize(24, 24)
        row3.addWidget(self._accent_3_preview)

        pick3_btn = QPushButton("Choose Color")
        pick3_btn.clicked.connect(lambda: self._pick_accent_color(3))
        row3.addWidget(pick3_btn)
        row3.addStretch()
        custom_form.addRow("Option 3 Accent (03 Flavor):", row3)

        # Reset button
        reset_row = QHBoxLayout()
        reset_btn = QPushButton("Reset to Preset Defaults")
        reset_btn.setIcon(get_vector_icon("reset", color="#8A8D98", size=13))
        reset_btn.clicked.connect(self._reset_theme_to_preset)
        reset_row.addWidget(reset_btn)
        reset_row.addStretch()
        custom_form.addRow("", reset_row)

        layout.addWidget(custom_group)
        layout.addStretch()

        self._update_preview_boxes()
        return widget

    def _update_preview_boxes(self):
        c1 = self._accent_1_input.text().strip() or "#FF453A"
        c2 = self._accent_2_input.text().strip() or "#30D158"
        c3 = self._accent_3_input.text().strip() or "#0A84FF"
        self._accent_1_preview.setStyleSheet(
            f"background-color: {c1}; border-radius: 4px; border: 1px solid rgba(255,255,255,0.25);"
        )
        self._accent_2_preview.setStyleSheet(
            f"background-color: {c2}; border-radius: 4px; border: 1px solid rgba(255,255,255,0.25);"
        )
        self._accent_3_preview.setStyleSheet(
            f"background-color: {c3}; border-radius: 4px; border: 1px solid rgba(255,255,255,0.25);"
        )

    def _pick_accent_color(self, index: int):
        inp = self._accent_1_input if index == 1 else (self._accent_2_input if index == 2 else self._accent_3_input)
        curr = QColor(inp.text().strip() if inp.text().strip().startswith("#") else "#FFFFFF")
        picked = QColorDialog.getColor(curr, self, f"Select Option {index} Accent Color")
        if picked.isValid():
            inp.setText(picked.name())
            self._on_custom_color_changed()

    def _on_preset_clicked(self, name: str):
        self._active_preset = name
        theme = PRESET_THEMES.get(name)
        if not theme:
            return

        for card_name, card in self._preset_cards.items():
            card.set_active(card_name == name, theme.accent_1)

        self._accent_1_input.blockSignals(True)
        self._accent_2_input.blockSignals(True)
        self._accent_3_input.blockSignals(True)

        self._accent_1_input.setText(theme.accent_1)
        self._accent_2_input.setText(theme.accent_2)
        self._accent_3_input.setText(theme.accent_3)

        self._accent_1_input.blockSignals(False)
        self._accent_2_input.blockSignals(False)
        self._accent_3_input.blockSignals(False)

        self._update_preview_boxes()

        # Live apply
        tm = ThemeManager.get_instance(self._config)
        tm.set_accents(theme.accent_1, theme.accent_2, theme.accent_3, preset_name=name, save=False)
        if self.parent() and hasattr(self.parent(), "apply_theme"):
            self.parent().apply_theme(tm.current_theme)

    def _on_custom_color_changed(self):
        self._update_preview_boxes()
        c1 = self._accent_1_input.text().strip()
        c2 = self._accent_2_input.text().strip()
        c3 = self._accent_3_input.text().strip()

        # Check if matches any preset exactly
        matched_preset = "Custom"
        for p_name, p_theme in PRESET_THEMES.items():
            if (
                p_theme.accent_1.lower() == c1.lower()
                and p_theme.accent_2.lower() == c2.lower()
                and p_theme.accent_3.lower() == c3.lower()
            ):
                matched_preset = p_name
                break

        self._active_preset = matched_preset
        for card_name, card in self._preset_cards.items():
            card.set_active(card_name == matched_preset, c1)

        tm = ThemeManager.get_instance(self._config)
        tm.set_accents(c1, c2, c3, preset_name=matched_preset, save=False)
        if self.parent() and hasattr(self.parent(), "apply_theme"):
            self.parent().apply_theme(tm.current_theme)

    def _reset_theme_to_preset(self):
        p_name = self._active_preset if self._active_preset in PRESET_THEMES else "Modern RP"
        self._on_preset_clicked(p_name)

    # ── 2. API Tab ───────────────────────────────────────

    def _create_api_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText("gsk_...")
        form.addRow("API Key:", self._api_key_input)

        get_key_btn = QPushButton("Dapatkan Groq API Key Gratis (console.groq.com/keys)")
        get_key_btn.setIcon(get_vector_icon("external_link", color="#FFFFFF", size=13))
        get_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        get_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #24262B;
                color: #FFFFFF;
                border: 1px solid #33363D;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 8.5pt;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2D3037;
                border-color: #5E6AD2;
            }
        """)
        get_key_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys")))
        form.addRow("", get_key_btn)

        self._model_input = QLineEdit("qwen/qwen3.8-27b")
        form.addRow("AI Model:", self._model_input)

        self._base_url_input = QLineEdit("https://api.groq.com/openai/v1")
        form.addRow("API Base URL:", self._base_url_input)

        self._ignore_words_input = QLineEdit()
        self._ignore_words_input.setPlaceholderText("Los Santos, LSPD, FIB...")
        form.addRow("Ignore Proper Nouns:", self._ignore_words_input)

        return widget

    # ── 3. Hotkeys Tab ───────────────────────────────────

    def _create_hotkeys_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        self._hotkey_ocr_input = QLineEdit("<f4>")
        form.addRow("OCR Input Bar (What You Type):", self._hotkey_ocr_input)

        self._hotkey_ocr_chatlog = QLineEdit("<f3>")
        form.addRow("OCR Chatlog (Incoming Messages):", self._hotkey_ocr_chatlog)

        self._hotkey_clipboard = QLineEdit("<f5>")
        form.addRow("Clipboard Capture:", self._hotkey_clipboard)

        self._hotkey_copy1 = QLineEdit("<ctrl>+1")
        form.addRow("Copy Option 1:", self._hotkey_copy1)

        self._hotkey_copy2 = QLineEdit("<ctrl>+2")
        form.addRow("Copy Option 2:", self._hotkey_copy2)

        self._hotkey_copy3 = QLineEdit("<ctrl>+3")
        form.addRow("Copy Option 3:", self._hotkey_copy3)

        self._hotkey_toggle = QLineEdit("<insert>")
        form.addRow("Toggle Window:", self._hotkey_toggle)

        self._hotkey_scroll_up = QLineEdit("<page_up>")
        form.addRow("OSD Scroll Up:", self._hotkey_scroll_up)

        self._hotkey_scroll_down = QLineEdit("<page_down>")
        form.addRow("OSD Scroll Down:", self._hotkey_scroll_down)

        return widget

    # ── 4. OCR Tab ───────────────────────────────────────

    def _create_ocr_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        path_row = QHBoxLayout()
        self._tesseract_path = QLineEdit()
        path_row.addWidget(self._tesseract_path)

        detect_btn = QPushButton("Auto-Detect")
        detect_btn.clicked.connect(self._auto_detect_tesseract)
        path_row.addWidget(detect_btn)
        layout.addLayout(path_row)

        # 1. Input Bar Zone (F4)
        input_group = QGroupBox("Input Typing Bar (F4 - What You Type)")
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(6)

        coord_row_1 = QHBoxLayout()
        self._input_left = QSpinBox()
        self._input_left.setRange(0, 9999)
        self._input_top = QSpinBox()
        self._input_top.setRange(0, 9999)
        self._input_width = QSpinBox()
        self._input_width.setRange(20, 9999)
        self._input_height = QSpinBox()
        self._input_height.setRange(15, 9999)

        coord_row_1.addWidget(QLabel("X:"))
        coord_row_1.addWidget(self._input_left)
        coord_row_1.addWidget(QLabel("Y:"))
        coord_row_1.addWidget(self._input_top)
        coord_row_1.addWidget(QLabel("W:"))
        coord_row_1.addWidget(self._input_width)
        coord_row_1.addWidget(QLabel("H:"))
        coord_row_1.addWidget(self._input_height)
        input_layout.addRow(coord_row_1)

        input_btn_row = QHBoxLayout()
        snip_input_btn = QPushButton("Snip Input Bar")
        snip_input_btn.setIcon(get_vector_icon("snip_input", color="#FFFFFF", size=14))
        snip_input_btn.setStyleSheet("background-color: #282A2E; color: #FFFFFF; font-weight: 600; border-radius: 9999px; padding: 6px 14px;")
        snip_input_btn.clicked.connect(lambda: self._start_snip("input"))
        input_btn_row.addWidget(snip_input_btn)

        test_input_btn = QPushButton("Test Input OCR")
        test_input_btn.setIcon(get_vector_icon("search", color="#8A8D98", size=14))
        test_input_btn.clicked.connect(lambda: self._run_test_ocr("input"))
        input_btn_row.addWidget(test_input_btn)
        input_layout.addRow(input_btn_row)

        layout.addWidget(input_group)

        # 2. Chatlog History Zone (F3)
        chat_group = QGroupBox("Chatlog History (F3 - Incoming Messages)")
        chat_layout = QFormLayout(chat_group)
        chat_layout.setSpacing(6)

        coord_row_2 = QHBoxLayout()
        self._chat_left = QSpinBox()
        self._chat_left.setRange(0, 9999)
        self._chat_top = QSpinBox()
        self._chat_top.setRange(0, 9999)
        self._chat_width = QSpinBox()
        self._chat_width.setRange(20, 9999)
        self._chat_height = QSpinBox()
        self._chat_height.setRange(15, 9999)

        coord_row_2.addWidget(QLabel("X:"))
        coord_row_2.addWidget(self._chat_left)
        coord_row_2.addWidget(QLabel("Y:"))
        coord_row_2.addWidget(self._chat_top)
        coord_row_2.addWidget(QLabel("W:"))
        coord_row_2.addWidget(self._chat_width)
        coord_row_2.addWidget(QLabel("H:"))
        coord_row_2.addWidget(self._chat_height)
        chat_layout.addRow(coord_row_2)

        chat_btn_row = QHBoxLayout()
        snip_chat_btn = QPushButton("Snip Chatlog")
        snip_chat_btn.setIcon(get_vector_icon("snip_chat", color="#FFFFFF", size=14))
        snip_chat_btn.setStyleSheet("background-color: #282A2E; color: #FFFFFF; font-weight: 600; border-radius: 9999px; padding: 6px 14px;")
        snip_chat_btn.clicked.connect(lambda: self._start_snip("chatlog"))
        chat_btn_row.addWidget(snip_chat_btn)

        test_chat_btn = QPushButton("Test Chatlog OCR")
        test_chat_btn.setIcon(get_vector_icon("search", color="#8A8D98", size=14))
        test_chat_btn.clicked.connect(lambda: self._run_test_ocr("chatlog"))
        chat_btn_row.addWidget(test_chat_btn)
        chat_layout.addRow(chat_btn_row)

        layout.addWidget(chat_group)

        self._show_bbox_check = QCheckBox("Show visual OCR capture frames on screen")
        layout.addWidget(self._show_bbox_check)

        self._test_output_lbl = QLabel("")
        self._test_output_lbl.setStyleSheet(
            "background-color: #151618; border: 1px solid #28292C; border-radius: 6px; padding: 8px; color: #FFFFFF;"
        )
        self._test_output_lbl.setWordWrap(True)
        self._test_output_lbl.hide()
        layout.addWidget(self._test_output_lbl)

        layout.addStretch()
        return widget

    def _auto_detect_tesseract(self):
        from ocr_engine import find_tesseract
        exe_path, _ = find_tesseract()
        if exe_path:
            self._tesseract_path.setText(exe_path)
            QMessageBox.information(self, "Tesseract Ditemukan", f"Tesseract OCR berhasil terdeteksi:\n{exe_path}")
        else:
            QMessageBox.warning(self, "Tidak Ditemukan", "Tesseract OCR tidak ditemukan secara otomatis.\nSilakan arahkan secara manual ke file tesseract.exe.")

    def _start_snip(self, mode: str):
        self._snip_mode = mode
        self._region_selector.start_selection()

    def _on_snip_selected(self, bbox: dict):
        if self._snip_mode == "input":
            self._input_left.setValue(bbox["left"])
            self._input_top.setValue(bbox["top"])
            self._input_width.setValue(bbox["width"])
            self._input_height.setValue(bbox["height"])
            self._run_test_ocr("input")
        else:
            self._chat_left.setValue(bbox["left"])
            self._chat_top.setValue(bbox["top"])
            self._chat_width.setValue(bbox["width"])
            self._chat_height.setValue(bbox["height"])
            self._run_test_ocr("chatlog")

    def _run_test_ocr(self, mode: str):
        from ocr_engine import OCREngine
        engine = OCREngine(self._tesseract_path.text().strip())
        if mode == "input":
            bbox = {
                "left": self._input_left.value(),
                "top": self._input_top.value(),
                "width": self._input_width.value(),
                "height": self._input_height.value(),
            }
            res = engine.clean_input_text(engine.capture_and_recognize(bbox, lang="ind+eng"))
            title = "Input Bar (F4)"
        else:
            bbox = {
                "left": self._chat_left.value(),
                "top": self._chat_top.value(),
                "width": self._chat_width.value(),
                "height": self._chat_height.value(),
            }
            res = engine.extract_latest_chat_line(engine.capture_and_recognize(bbox, lang="ind+eng"))
            title = "Chatlog Latest Line (F3)"

        self._test_output_lbl.show()
        if res:
            self._test_output_lbl.setText(f"[{title}] Detected:\n\"{res}\"")
        else:
            self._test_output_lbl.setText(f"[{title}] No text detected in this region.")

    # ── 5. OSD Tab ───────────────────────────────────────

    def _create_osd_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        self._osd_enabled = QCheckBox("Enable In-Game Overlay (OSD)")
        layout.addWidget(self._osd_enabled)

        pos_group = QGroupBox("Position and Size")
        pos_form = QFormLayout(pos_group)
        pos_form.setSpacing(8)

        self._osd_left = QSpinBox()
        self._osd_left.setRange(-9999, 9999)
        pos_form.addRow("Left (X):", self._osd_left)

        self._osd_top = QSpinBox()
        self._osd_top.setRange(-9999, 9999)
        pos_form.addRow("Top (Y):", self._osd_top)

        self._osd_width = QSpinBox()
        self._osd_width.setRange(100, 9999)
        pos_form.addRow("Width:", self._osd_width)

        self._osd_height = QSpinBox()
        self._osd_height.setRange(50, 9999)
        pos_form.addRow("Height:", self._osd_height)

        layout.addWidget(pos_group)

        app_group = QGroupBox("Appearance")
        app_form = QFormLayout(app_group)
        app_form.setSpacing(8)

        color_row = QHBoxLayout()
        self._osd_color_input = QLineEdit("#FFFFFF")
        self._osd_color_input.setMaximumWidth(120)
        color_row.addWidget(self._osd_color_input)

        pick_btn = QPushButton("Select Color")
        pick_btn.clicked.connect(self._pick_color)
        color_row.addWidget(pick_btn)

        self._color_preview = QLabel("  ")
        self._color_preview.setFixedSize(26, 26)
        self._color_preview.setStyleSheet("background-color: #FFFFFF; border-radius: 4px; border: 1px solid #28292C;")
        color_row.addWidget(self._color_preview)
        color_row.addStretch()

        app_form.addRow("Text Color:", color_row)

        self._osd_font_size = QSpinBox()
        self._osd_font_size.setRange(8, 48)
        self._osd_font_size.setValue(12)
        app_form.addRow("Font Size:", self._osd_font_size)

        self._osd_duration = QSpinBox()
        self._osd_duration.setRange(0, 300)
        self._osd_duration.setValue(12)
        self._osd_duration.setSuffix(" sec")
        app_form.addRow("Auto-Hide Duration:", self._osd_duration)

        layout.addWidget(app_group)
        layout.addStretch()
        return widget

    def _pick_color(self):
        current = QColor(self._osd_color_input.text())
        color = QColorDialog.getColor(current, self, "Choose OSD Font Color")
        if color.isValid():
            self._osd_color_input.setText(color.name())
            self._color_preview.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")

    # ── 6. Styles Tab ────────────────────────────────────

    def _create_styles_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        self._style_list = QListWidget()
        layout.addWidget(self._style_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Style")
        add_btn.setIcon(get_vector_icon("add", color="#FFFFFF", size=14))
        add_btn.clicked.connect(self._add_style)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("Edit Style")
        edit_btn.setIcon(get_vector_icon("edit", color="#FFFFFF", size=14))
        edit_btn.clicked.connect(self._edit_style)
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("Delete")
        del_btn.setIcon(get_vector_icon("clear", color="#8A8D98", size=13))
        del_btn.clicked.connect(self._delete_style)
        btn_row.addWidget(del_btn)

        layout.addLayout(btn_row)
        return widget

    def _refresh_style_list(self):
        self._style_list.clear()
        if self._style_manager:
            for name in self._style_manager.get_style_names():
                self._style_list.addItem(name)

    def _add_style(self):
        dlg = StyleEditorDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_style_data()
            if self._style_manager:
                self._style_manager.add_style(
                    data["name"], data["rule"], data["tone"], data["intensity"]
                )
                self._refresh_style_list()

    def _edit_style(self):
        item = self._style_list.currentItem()
        if not item or not self._style_manager:
            return
        name = item.text()
        style_data = self._style_manager.get_style(name)
        if style_data:
            dlg = StyleEditorDialog(style_data=style_data, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_style_data()
                self._style_manager.update_style(
                    name, data["name"], data["rule"], data["tone"], data["intensity"]
                )
                self._refresh_style_list()

    def _delete_style(self):
        item = self._style_list.currentItem()
        if not item or not self._style_manager:
            return
        name = item.text()
        if QMessageBox.question(self, "Delete Style", f"Delete style '{name}'?") == QMessageBox.StandardButton.Yes:
            self._style_manager.delete_style(name)
            self._refresh_style_list()

    # ── Load & Gather Settings ───────────────────────────

    def _load_settings(self):
        if not self._config:
            return
        cfg = self._config.config if hasattr(self._config, "config") else {}

        # Theme Accents
        theme_cfg = cfg.get("theme", {})
        if isinstance(theme_cfg, dict):
            preset_name = theme_cfg.get("preset", "Modern RP")
            self._active_preset = preset_name
            self._accent_1_input.setText(theme_cfg.get("accent_1") or theme_cfg.get("primary_accent") or "#FF453A")
            self._accent_2_input.setText(theme_cfg.get("accent_2") or theme_cfg.get("secondary_accent") or "#30D158")
            self._accent_3_input.setText(theme_cfg.get("accent_3") or theme_cfg.get("tertiary_accent") or "#0A84FF")
        else:
            self._active_preset = "Modern RP"
            self._accent_1_input.setText("#FF453A")
            self._accent_2_input.setText("#30D158")
            self._accent_3_input.setText("#0A84FF")

        if self._active_preset in self._preset_cards:
            self._preset_cards[self._active_preset].set_active(True, self._accent_1_input.text())
        self._update_preview_boxes()

        # API
        self._api_key_input.setText(cfg.get("api_key", ""))
        self._model_input.setText(cfg.get("ai_model") or cfg.get("model", "qwen/qwen3.8-27b"))
        self._base_url_input.setText(cfg.get("api_base_url") or cfg.get("base_url", "https://api.groq.com/openai/v1"))
        ignore_words = cfg.get("ignore_words", [])
        self._ignore_words_input.setText(", ".join(ignore_words) if isinstance(ignore_words, list) else "")

        # Hotkeys
        hk = cfg.get("hotkeys", {})
        self._hotkey_ocr_input.setText(cfg.get("hotkey_ocr_input") or cfg.get("hotkey_ocr") or hk.get("ocr_input", "<f4>"))
        self._hotkey_ocr_chatlog.setText(cfg.get("hotkey_ocr_chatlog") or hk.get("ocr_chatlog", "<f3>"))
        self._hotkey_clipboard.setText(cfg.get("hotkey_clipboard") or hk.get("clipboard_capture", "<f5>"))
        self._hotkey_copy1.setText(cfg.get("hotkey_ans1") or hk.get("copy_answer_1", "<ctrl>+1"))
        self._hotkey_copy2.setText(cfg.get("hotkey_ans2") or hk.get("copy_answer_2", "<ctrl>+2"))
        self._hotkey_copy3.setText(cfg.get("hotkey_ans3") or hk.get("copy_answer_3", "<ctrl>+3"))
        self._hotkey_toggle.setText(cfg.get("hotkey_toggle_window") or hk.get("toggle_window", "<insert>"))
        self._hotkey_scroll_up.setText(cfg.get("hotkey_scroll_up") or hk.get("scroll_up", "<page_up>"))
        self._hotkey_scroll_down.setText(cfg.get("hotkey_scroll_down") or hk.get("scroll_down", "<page_down>"))

        # OCR
        self._tesseract_path.setText(
            cfg.get("tesseract_path", r"C:\Program Files (x86)\PRORP Translator\tesseract\tesseract.exe")
        )
        input_bbox = cfg.get("input_bbox") or cfg.get("bbox") or cfg.get("ocr_bbox", {})
        self._input_left.setValue(input_bbox.get("left", 265))
        self._input_top.setValue(input_bbox.get("top", 350))
        self._input_width.setValue(input_bbox.get("width", 645))
        self._input_height.setValue(input_bbox.get("height", 45))

        chat_bbox = cfg.get("chatlog_bbox", {})
        self._chat_left.setValue(chat_bbox.get("left", 265))
        self._chat_top.setValue(chat_bbox.get("top", 200))
        self._chat_width.setValue(chat_bbox.get("width", 645))
        self._chat_height.setValue(chat_bbox.get("height", 140))
        self._show_bbox_check.setChecked(cfg.get("show_bbox_overlay", False) or cfg.get("show_ocr_bbox", False))

        # OSD
        self._osd_enabled.setChecked(cfg.get("osd_enabled", True))
        osd_bbox = cfg.get("osd_bbox", {})
        self._osd_left.setValue(osd_bbox.get("left", 100))
        self._osd_top.setValue(osd_bbox.get("top", 100))
        self._osd_width.setValue(osd_bbox.get("width", 420))
        self._osd_height.setValue(osd_bbox.get("height", 220))
        self._osd_color_input.setText(cfg.get("osd_font_color", "#FFFFFF"))
        self._osd_font_size.setValue(cfg.get("osd_font_size", 12))
        self._osd_duration.setValue(cfg.get("osd_duration", 12))
        self._color_preview.setStyleSheet(f"background-color: {self._osd_color_input.text()}; border-radius: 4px;")

        self._refresh_style_list()

    def _gather_settings(self) -> dict:
        ignore_text = self._ignore_words_input.text().strip()
        ignore_words = [w.strip() for w in ignore_text.split(",") if w.strip()] if ignore_text else []

        input_bbox = {
            "left": self._input_left.value(),
            "top": self._input_top.value(),
            "width": self._input_width.value(),
            "height": self._input_height.value(),
        }

        chatlog_bbox = {
            "left": self._chat_left.value(),
            "top": self._chat_top.value(),
            "width": self._chat_width.value(),
            "height": self._chat_height.value(),
        }

        osd_bbox = {
            "left": self._osd_left.value(),
            "top": self._osd_top.value(),
            "width": self._osd_width.value(),
            "height": self._osd_height.value(),
        }

        theme_data = {
            "preset": self._active_preset,
            "accent_1": self._accent_1_input.text().strip() or "#FF453A",
            "accent_2": self._accent_2_input.text().strip() or "#30D158",
            "accent_3": self._accent_3_input.text().strip() or "#0A84FF",
        }

        return {
            "theme": theme_data,
            "api_key": self._api_key_input.text().strip(),
            "ai_model": self._model_input.text().strip() or "qwen/qwen3.8-27b",
            "model": self._model_input.text().strip() or "qwen/qwen3.8-27b",
            "api_base_url": self._base_url_input.text().strip() or "https://api.groq.com/openai/v1",
            "base_url": self._base_url_input.text().strip() or "https://api.groq.com/openai/v1",
            "ignore_words": ignore_words,
            "hotkey_ocr": self._hotkey_ocr_input.text().strip() or "<f4>",
            "hotkey_ocr_input": self._hotkey_ocr_input.text().strip() or "<f4>",
            "hotkey_ocr_chatlog": self._hotkey_ocr_chatlog.text().strip() or "<f3>",
            "hotkey_clipboard": self._hotkey_clipboard.text().strip() or "<f5>",
            "hotkey_ans1": self._hotkey_copy1.text().strip() or "<ctrl>+1",
            "hotkey_ans2": self._hotkey_copy2.text().strip() or "<ctrl>+2",
            "hotkey_ans3": self._hotkey_copy3.text().strip() or "<ctrl>+3",
            "hotkey_toggle_window": self._hotkey_toggle.text().strip() or "<insert>",
            "hotkey_scroll_up": self._hotkey_scroll_up.text().strip() or "<page_up>",
            "hotkey_scroll_down": self._hotkey_scroll_down.text().strip() or "<page_down>",
            "tesseract_path": self._tesseract_path.text().strip(),
            "input_bbox": input_bbox,
            "chatlog_bbox": chatlog_bbox,
            "bbox": input_bbox,
            "ocr_bbox": input_bbox,
            "show_bbox_overlay": self._show_bbox_check.isChecked(),
            "show_ocr_bbox": self._show_bbox_check.isChecked(),
            "osd_enabled": self._osd_enabled.isChecked(),
            "osd_bbox": osd_bbox,
            "osd_font_color": self._osd_color_input.text().strip() or "#FFFFFF",
            "osd_font_size": self._osd_font_size.value(),
            "osd_duration": self._osd_duration.value(),
        }

    def _on_apply(self):
        settings = self._gather_settings()
        # Direct save of theme to ThemeManager to guarantee permanence
        tm = ThemeManager.get_instance(self._config)
        t_data = settings["theme"]
        tm.set_accents(
            t_data["accent_1"],
            t_data["accent_2"],
            t_data["accent_3"],
            preset_name=t_data["preset"],
            save=True,
        )
        self.settings_applied.emit(settings)

    def _on_ok(self):
        self._on_apply()
        self.accept()

    def reject(self):
        # Revert to config values on cancel
        tm = ThemeManager.get_instance(self._config)
        tm.load_from_config()
        if self.parent() and hasattr(self.parent(), "apply_theme"):
            self.parent().apply_theme(tm.current_theme)
        super().reject()

    def get_settings(self) -> dict:
        return self._gather_settings()
