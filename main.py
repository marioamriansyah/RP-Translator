"""
PRORP Translator - Main Entry Point

GTA RP translation tool that translates Indonesian text to English
in various roleplay styles.
"""

import sys
import os

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Prevent crash under pythonw.exe where stdout and stderr are None, log to app.log
log_file_path = os.path.join(APP_DIR, "app.log")
if sys.stdout is None:
    try:
        sys.stdout = open(log_file_path, "a", encoding="utf-8", buffering=1)
    except Exception:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    try:
        sys.stderr = open(log_file_path, "a", encoding="utf-8", buffering=1)
    except Exception:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config_manager import ConfigManager
from translator import Translator
from ocr_engine import OCREngine
from hotkey_manager import HotkeyManager
from style_manager import StyleManager
from app import AppController


def main():
    """Application entry point."""

    # High DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    # Set Windows Per-Monitor DPI Awareness (ensures accurate screen capture on Windows 10/11)
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("rpplus.translator.app.1.0.3")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("RP+ Translator")
    app.setOrganizationName("RP Plus")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    # Set application-wide icon from assets/app_icon.ico
    from ui.vector_icons import get_app_qicon
    app.setWindowIcon(get_app_qicon())

    # Set default font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # ── Initialize Managers ────────────────────────────
    config_path = os.path.join(APP_DIR, "config.json")
    config_manager = ConfigManager(config_path)

    style_manager = StyleManager(config_manager)
    translator = Translator(config_manager)
    ocr_engine = OCREngine(config_manager)
    hotkey_manager = HotkeyManager(config_manager)

    # ── Create App Controller ──────────────────────────
    controller = AppController(
        config_manager=config_manager,
        translator=translator,
        ocr_engine=ocr_engine,
        hotkey_manager=hotkey_manager,
        style_manager=style_manager,
    )

    # Show main window
    controller.show()

    # Start global hotkeys
    controller.start_hotkeys()

    # ── Run ────────────────────────────────────────────
    try:
        exit_code = app.exec()
    finally:
        controller.stop_hotkeys()
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(os.path.join(APP_DIR, "crash.log"), "w", encoding="utf-8") as f:
            import traceback
            traceback.print_exc(file=f)
