"""
Theme Manager for PRORP Translator - Accent Theme System.

Provides simplified, bulletproof accent customization:
- Presets: Modern RP (Illustrator default), Linear Classic, Cyber Neon,
  Emerald Tactical, Monochrome Pro, Dracula Synth
- 3 Dedicated Option Accents (Card 1 / Card 2 / Card 3)
- Real-time updates with permanent persistence (no accidental reverting)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class AccentTheme:
    name: str
    description: str
    accent_1: str  # Card 1 (01 Natural)
    accent_2: str  # Card 2 (02 Street)
    accent_3: str  # Card 3 (03 Flavor)

    # Fallback properties for backward compatibility
    @property
    def accent_primary(self) -> str:
        return self.accent_1

    @property
    def accent_secondary(self) -> str:
        return self.accent_2

    @property
    def accent_tertiary(self) -> str:
        return self.accent_3

    @property
    def text_primary(self) -> str:
        return "#FFFFFF"

    @property
    def text_secondary(self) -> str:
        return "#8A8D98"

    @property
    def text_muted(self) -> str:
        return "#656872"

    @property
    def bg_primary(self) -> str:
        return "#141517"

    @property
    def bg_card(self) -> str:
        return "#1E1F21"

    @property
    def border_base(self) -> str:
        return "#28292C"

    @property
    def btn_primary_bg(self) -> str:
        return "#D0D3DA"

    @property
    def btn_primary_fg(self) -> str:
        return "#141517"


# Built-in Accent Presets
PRESET_THEMES: dict[str, AccentTheme] = {
    "Modern RP": AccentTheme(
        name="Modern RP",
        description="Official RP+ palette (Coral Red, Emerald Lime, Azure Blue)",
        accent_1="#FF453A",
        accent_2="#30D158",
        accent_3="#0A84FF",
    ),
    "Linear Classic": AccentTheme(
        name="Linear Classic",
        description="Linear design system (Violet, Brand Pink, Mint Green)",
        accent_1="#5E6AD2",
        accent_2="#F91880",
        accent_3="#00BA7C",
    ),
    "Cyber Neon": AccentTheme(
        name="Cyber Neon",
        description="High-contrast Night City neon (Cyan, Magenta, Yellow)",
        accent_1="#00E5FF",
        accent_2="#FF2A85",
        accent_3="#FFE600",
    ),
    "Emerald Tactical": AccentTheme(
        name="Emerald Tactical",
        description="Special Forces tactical HUD (Tactical Mint, Amber, Cyan)",
        accent_1="#10B981",
        accent_2="#F59E0B",
        accent_3="#06B6D4",
    ),
    "Monochrome Pro": AccentTheme(
        name="Monochrome Pro",
        description="Leica / Apple Pro titanium (White, Silver, Zinc)",
        accent_1="#FFFFFF",
        accent_2="#D4D4D8",
        accent_3="#A1A1AA",
    ),
    "Dracula Synth": AccentTheme(
        name="Dracula Synth",
        description="Dark synthwave (Electric Purple, Hot Pink, Radioactive Green)",
        accent_1="#BD93F9",
        accent_2="#FF79C6",
        accent_3="#50FA7B",
    ),
}

# Theme aliases for backward compatibility
Theme = AccentTheme


def _is_light_color(hex_color: str) -> bool:
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0 > 0.6
    except Exception:
        pass
    return False


class ThemeManager(QObject):
    """
    Central Coordinator for Application Accents.
    Maintains accent_1, accent_2, accent_3 and ensures they persist correctly.
    """

    theme_changed = pyqtSignal(object)  # AccentTheme

    _instance: Optional[ThemeManager] = None

    @classmethod
    def get_instance(cls, config_manager=None) -> ThemeManager:
        if cls._instance is None:
            cls._instance = cls(config_manager)
        elif config_manager and not cls._instance._config:
            cls._instance._config = config_manager
            cls._instance.load_from_config()
        return cls._instance

    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self._config = config_manager

        # Default is Modern RP from user's Illustrator design
        default = PRESET_THEMES["Modern RP"]
        self._current_preset = "Modern RP"
        self._accent_1 = default.accent_1
        self._accent_2 = default.accent_2
        self._accent_3 = default.accent_3

        if self._config:
            self.load_from_config()

    @property
    def current_theme(self) -> AccentTheme:
        return AccentTheme(
            name=self._current_preset,
            description="Custom or Preset Accent Palette",
            accent_1=self._accent_1,
            accent_2=self._accent_2,
            accent_3=self._accent_3,
        )

    # Convenience properties
    @property
    def accent_1(self) -> str:
        return self._accent_1

    @property
    def accent_2(self) -> str:
        return self._accent_2

    @property
    def accent_3(self) -> str:
        return self._accent_3

    @property
    def accent_primary(self) -> str:
        return self._accent_1

    @property
    def accent_secondary(self) -> str:
        return self._accent_2

    @property
    def accent_tertiary(self) -> str:
        return self._accent_3

    # Theme colors for backward compatibility
    bg_primary = "#141517"
    bg_surface = "#18191B"
    bg_card = "#1E1F21"
    bg_card_hover = "#252629"
    bg_input = "#151618"
    bg_pill_inactive = "#222326"
    border_base = "#2A2B2E"
    border_card = "#2A2B2E"
    border_hover = "#3A3B40"
    border_focus = "#5E6AD2"
    text_primary = "#FFFFFF"
    text_emphasis = "#FFFFFF"
    text_secondary = "#8A8D98"
    text_muted = "#656872"
    text_dark = "#141517"
    btn_primary_bg = "#D0D3DA"
    btn_primary_fg = "#141517"

    def get_theme_names(self) -> list[str]:
        return list(PRESET_THEMES.keys())

    def set_preset(self, preset_name: str, save: bool = True) -> AccentTheme:
        if preset_name in PRESET_THEMES:
            p = PRESET_THEMES[preset_name]
            self._current_preset = preset_name
            self._accent_1 = p.accent_1
            self._accent_2 = p.accent_2
            self._accent_3 = p.accent_3
            if save and self._config:
                self.save_to_config()
            self.theme_changed.emit(self.current_theme)
        return self.current_theme

    def set_accents(
        self,
        accent_1: str,
        accent_2: str,
        accent_3: str,
        preset_name: Optional[str] = None,
        save: bool = True,
    ) -> AccentTheme:
        self._accent_1 = accent_1.strip() or "#FF453A"
        self._accent_2 = accent_2.strip() or "#30D158"
        self._accent_3 = accent_3.strip() or "#0A84FF"
        if preset_name:
            self._current_preset = preset_name
        if save and self._config:
            self.save_to_config()
        self.theme_changed.emit(self.current_theme)
        return self.current_theme

    def load_from_config(self):
        if not self._config:
            return
        cfg = self._config.config if hasattr(self._config, "config") else {}
        t_data = cfg.get("theme", {})
        if isinstance(t_data, dict) and t_data:
            self._current_preset = t_data.get("preset", "Modern RP")
            # Always respect custom accent colors if present
            self._accent_1 = t_data.get("accent_1") or t_data.get("primary_accent") or "#FF453A"
            self._accent_2 = t_data.get("accent_2") or t_data.get("secondary_accent") or "#30D158"
            self._accent_3 = t_data.get("accent_3") or t_data.get("tertiary_accent") or "#0A84FF"
        else:
            default = PRESET_THEMES["Modern RP"]
            self._current_preset = "Modern RP"
            self._accent_1 = default.accent_1
            self._accent_2 = default.accent_2
            self._accent_3 = default.accent_3

    def save_to_config(self):
        if not self._config:
            return
        theme_data = {
            "preset": self._current_preset,
            "accent_1": self._accent_1,
            "accent_2": self._accent_2,
            "accent_3": self._accent_3,
        }
        self._config.set("theme", theme_data, auto_save=True)

    # ── Dynamic Stylesheet Generators ──────────────────────────────────

    def get_main_window_qss(self, theme: Optional[AccentTheme] = None) -> str:
        return """
QMainWindow {
    background-color: #141517;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #FFFFFF;
}

/* Card Container */
QFrame#cardFrame {
    background-color: #1E1F21;
    border: 1px solid #28292C;
    border-radius: 16px;
}
QFrame#cardFrame:hover {
    border-color: #38393E;
}

/* Top Pill Toolbar */
QFrame#pillToolbar {
    background-color: #1E1F21;
    border: 1px solid #28292C;
    border-radius: 19px;
    padding: 3px 5px;
}

QPushButton#toolbarBtn {
    background-color: transparent;
    color: #FFFFFF;
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 5px 12px;
    font-size: 8.5pt;
    font-weight: 600;
}
QPushButton#toolbarBtn:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid transparent;
    border-radius: 14px;
}
QPushButton#toolbarBtn[active="true"] {
    background-color: #D4D4D8;
    color: #141517;
    border: 1px solid #D4D4D8;
    border-radius: 14px;
    font-weight: 700;
}
QPushButton#toolbarBtn[active="true"]:hover {
    background-color: #FFFFFF;
    color: #141517;
    border: 1px solid #FFFFFF;
    border-radius: 14px;
}

/* Recessed Input Field */
QFrame#inputFieldBox {
    background-color: #151618;
    border: 1px solid #28292C;
    border-radius: 14px;
    padding: 4px 8px;
}
QFrame#inputFieldBox:focus-within {
    border-color: #4A4D55;
}

QTextEdit#inputEdit {
    background-color: transparent;
    color: #FFFFFF;
    border: none;
    font-size: 10pt;
    line-height: 1.45;
}

/* Clear Button */
QPushButton#clearPillBtn {
    background-color: #282A2E;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 8pt;
    font-weight: 600;
}
QPushButton#clearPillBtn:hover {
    background-color: #383B42;
}

/* Circular Translate Action Button */
QPushButton#circleTranslateBtn {
    background-color: #D0D3DA;
    color: #141517;
    border: none;
    border-radius: 18px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
    font-size: 11pt;
    font-weight: 800;
}
QPushButton#circleTranslateBtn:hover {
    background-color: #FFFFFF;
}
QPushButton#circleTranslateBtn:pressed {
    background-color: #A0A3AA;
}
QPushButton#circleTranslateBtn:disabled {
    background-color: #252629;
    color: #55575D;
}

/* Style Dropdown Combo inside Input Bar */
QComboBox#styleSelectorCombo {
    background-color: transparent;
    color: #A0A3AD;
    border: none;
    font-size: 9pt;
    font-weight: 600;
    padding-right: 4px;
}
QComboBox#styleSelectorCombo:hover {
    color: #FFFFFF;
}
QComboBox#styleSelectorCombo::drop-down {
    border: none;
    width: 14px;
}
QComboBox#styleSelectorCombo QAbstractItemView {
    background-color: #1E1F21;
    color: #FFFFFF;
    border: 1px solid #2E3035;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #2C2D32;
}

/* Card Copy Pill Button */
QPushButton#cardCopyBtn {
    background-color: #282A2E;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 5px 14px;
    font-size: 8.5pt;
    font-weight: 600;
}
QPushButton#cardCopyBtn:hover {
    background-color: #383B42;
}

/* Footer Frame */
QFrame#footerFrame {
    background-color: transparent;
    border: none;
}
"""

    def get_settings_qss(self, theme: Optional[AccentTheme] = None) -> str:
        t = theme or self.current_theme
        acc = t.accent_1
        return f"""
QDialog {{
    background-color: #141517;
    color: #FFFFFF;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 9.5pt;
}}

QTabWidget::pane {{
    background-color: #1E1F21;
    border: 1px solid #28292C;
    border-radius: 12px;
    padding: 12px;
}}

QTabBar::tab {{
    background-color: #161719;
    color: #8A8D98;
    border: 1px solid #28292C;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 18px;
    margin-right: 4px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: #1E1F21;
    color: #FFFFFF;
    border: 1px solid #28292C;
    border-bottom: 2px solid {acc};
    font-weight: 700;
}}

QTabBar::tab:hover:!selected {{
    background-color: rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
}}

QLabel {{
    color: #D0D3DC;
    font-size: 9pt;
}}

QLineEdit, QSpinBox, QComboBox {{
    background-color: #151618;
    color: #FFFFFF;
    border: 1px solid #28292C;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 9pt;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {acc};
}}

QGroupBox {{
    color: #8A8D98;
    border: 1px solid #28292C;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

QCheckBox {{
    color: #FFFFFF;
    font-size: 9pt;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #38393E;
    background-color: #151618;
}}

QCheckBox::indicator:checked {{
    background-color: {acc};
    border-color: {acc};
}}

QPushButton {{
    background-color: #282A2E;
    color: #FFFFFF;
    border: 1px solid #28292C;
    border-radius: 9999px;
    padding: 6px 16px;
    font-size: 9pt;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #383B42;
    border-color: #4A4D55;
}}

QListWidget {{
    background-color: #151618;
    color: #FFFFFF;
    border: 1px solid #28292C;
    border-radius: 8px;
    padding: 4px;
}}

QListWidget::item {{
    border-radius: 4px;
    padding: 6px 10px;
}}

QListWidget::item:selected {{
    background-color: {acc};
    color: #ffffff;
    font-weight: 600;
}}
"""
