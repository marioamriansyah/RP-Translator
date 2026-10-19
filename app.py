"""
Application Controller - Coordinates all PRORP Translator components.

Owns all managers and UI. Handles translation workflow:
OCR → translate → display → OSD
"""

import traceback
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from osd_overlay import OSDOverlay


class TranslationWorker(QThread):
    """Background worker for AI translation to avoid UI freeze."""

    finished = pyqtSignal(list)       # [ans1, ans2, ans3]
    error = pyqtSignal(str)           # error message

    def __init__(self, translator, text: str, style_name: str, parent=None):
        super().__init__(parent)
        self._translator = translator
        self._text = text
        self._style_name = style_name

    def run(self):
        """Execute translation in background thread."""
        try:
            results = self._translator.translate(self._text, self._style_name)
            if isinstance(results, list) and len(results) >= 3:
                self.finished.emit(results[:3])
            elif isinstance(results, list):
                # Pad with empty strings if fewer than 3
                padded = results + [""] * (3 - len(results))
                self.finished.emit(padded)
            else:
                self.error.emit("Unexpected translation result format")
        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")


class MeaningWorker(QThread):
    """Background worker for F1 incoming RP chat meaning translation."""

    finished = pyqtSignal(str, str)  # (source_text, meaning_text)
    error = pyqtSignal(str)          # error message

    def __init__(self, translator, text: str, parent=None):
        super().__init__(parent)
        self._translator = translator
        self._text = text

    def run(self):
        """Execute English -> Indonesian RP meaning translation in background."""
        try:
            meaning = self._translator.translate_to_indonesian(self._text)
            self.finished.emit(self._text, meaning)
        except Exception as e:
            self.error.emit(f"Meaning translation error: {str(e)}")


class AppController(QObject):
    """Main application controller that wires all components together."""

    def __init__(
        self,
        config_manager,
        translator,
        ocr_engine,
        hotkey_manager,
        style_manager,
        parent=None,
    ):
        super().__init__(parent)

        self._config = config_manager
        self._translator = translator
        self._ocr = ocr_engine
        self._hotkeys = hotkey_manager
        self._styles = style_manager

        self._worker = None  # current translation worker
        self._pending_translate_text = None

        # Initialize Theme Manager and wire dynamic theme propagation
        from ui.theme_manager import ThemeManager
        self._theme_manager = ThemeManager.get_instance(self._config)

        # Create UI components
        self._window = MainWindow(
            config_manager=self._config,
            style_manager=self._styles,
        )
        self._osd = OSDOverlay(config_manager=self._config)

        self._theme_manager.theme_changed.connect(self._window.apply_theme)
        self._theme_manager.theme_changed.connect(self._osd.apply_theme)

        # Wire signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect all signals between components."""

        # Main window signals
        self._window.translate_requested.connect(self._on_translate)
        self._window.style_changed.connect(self._on_style_changed)
        self._window.copy_answer.connect(self._on_copy_answer)
        self._window.settings_requested.connect(lambda: self._on_settings(initial_tab=1))
        if hasattr(self._window, "theme_settings_requested"):
            self._window.theme_settings_requested.connect(lambda: self._on_settings(initial_tab=0))
        if hasattr(self._window, "position_osd_requested"):
            self._window.position_osd_requested.connect(self._osd.show_preview)

        # Hotkey signals
        try:
            if hasattr(self._hotkeys, "ocr_input"):
                self._hotkeys.ocr_input.connect(self._on_ocr_input_capture)
            elif hasattr(self._hotkeys, "ocr_capture"):
                self._hotkeys.ocr_capture.connect(self._on_ocr_capture)
            if hasattr(self._hotkeys, "ocr_chatlog"):
                self._hotkeys.ocr_chatlog.connect(self._on_ocr_chatlog_capture)
            if hasattr(self._hotkeys, "ocr_meaning"):
                self._hotkeys.ocr_meaning.connect(self._on_ocr_meaning_capture)
            self._hotkeys.copy_answer_1.connect(lambda: self._on_copy_answer(0))
            self._hotkeys.copy_answer_2.connect(lambda: self._on_copy_answer(1))
            self._hotkeys.copy_answer_3.connect(lambda: self._on_copy_answer(2))
            self._hotkeys.toggle_window.connect(self._window.toggle_visibility)
            self._hotkeys.scroll_up.connect(self._osd.scroll_up)
            self._hotkeys.scroll_down.connect(self._osd.scroll_down)
        except AttributeError as e:
            # Hotkey manager signals might not be set up yet
            print(f"[AppController] Warning: Hotkey signal connection error: {e}")

    # ── Translation ─────────────────────────────────────

    @pyqtSlot(str)
    def _on_translate(self, text: str):
        """Start translation in background thread."""
        if not text.strip():
            return

        if self._worker and self._worker.isRunning():
            self._window.set_status("Translation already in progress...")
            return

        self._pending_translate_text = text
        style_name = self._window.get_selected_style()
        self._window.set_translating(True)
        self._window.set_status(f"Translating with style: {style_name}...")

        # Check slang library first (synchronous, fast)
        try:
            slang_result = self._translator.check_slang_library(text, style_name)
            if slang_result:
                # Found in slang library, no API call needed
                self._pending_translate_text = None
                self._window.set_answers(
                    slang_result[0] if len(slang_result) > 0 else "",
                    slang_result[1] if len(slang_result) > 1 else "",
                    slang_result[2] if len(slang_result) > 2 else "",
                )
                self._window.set_translating(False)
                self._window.set_status("Found in slang library (instant)")
                self._show_on_osd(slang_result)
                return
        except (AttributeError, TypeError):
            # Translator might not have slang library method
            pass

        # Start AI translation in background
        self._worker = TranslationWorker(
            self._translator, text, style_name, parent=self
        )
        self._worker.finished.connect(self._on_translation_done)
        self._worker.error.connect(self._on_translation_error)
        self._worker.start()

    @pyqtSlot(list)
    def _on_translation_done(self, results: list):
        """Handle completed translation."""
        self._pending_translate_text = None
        self._window.set_answers(
            results[0] if len(results) > 0 else "",
            results[1] if len(results) > 1 else "",
            results[2] if len(results) > 2 else "",
        )
        self._window.set_translating(False)
        self._window.set_status("Translation complete")
        self._show_on_osd(results)
        self._cleanup_worker()

    @pyqtSlot(str)
    def _on_translation_error(self, error_msg: str):
        """Handle translation error and automatically prompt API key popup on 401 Unauthorized."""
        self._window.set_translating(False)
        self._window.set_status(f"Error: {error_msg}")
        self._cleanup_worker()

        err_lower = error_msg.lower()
        if (
            "401" in error_msg
            or "unauthorized" in err_lower
            or "api key is missing" in err_lower
            or "invalid_api_key" in err_lower
            or "invalid api key" in err_lower
        ):
            self.show_api_key_dialog(is_error=True, error_detail=error_msg)

    def show_api_key_dialog(self, is_error: bool = False, error_detail: str = ""):
        """Show modern popup dialog for configuring or updating Groq API Key."""
        from ui.api_key_dialog import ApiKeyDialog
        dialog = ApiKeyDialog(
            config_manager=self._config,
            is_error=is_error,
            error_detail=error_detail,
            parent=self._window,
        )
        dialog.api_key_saved.connect(self._on_api_key_saved)
        dialog.exec()

    @pyqtSlot(str)
    def _on_api_key_saved(self, new_key: str):
        """Handle new API key saved from popup dialog."""
        self._window.set_status("Groq API Key berhasil diaktifkan")
        if getattr(self, "_pending_translate_text", None):
            retry_text = self._pending_translate_text
            self._pending_translate_text = None
            self._on_translate(retry_text)

    def _cleanup_worker(self):
        """Clean up the translation worker."""
        if self._worker:
            self._worker.finished.disconnect()
            self._worker.error.disconnect()
            self._worker.deleteLater()
            self._worker = None

    def _show_on_osd(self, results: list):
        """Display results on the OSD overlay."""
        lines = []
        for i, r in enumerate(results):
            if r:
                lines.append(f"[{i+1}] {r}")
        if lines:
            self._osd.show_translation("\n".join(lines))

    # ── OCR ─────────────────────────────────────────────

    @pyqtSlot()
    def _on_ocr_input_capture(self):
        """Capture text typed by the player in the chat input bar (F4) and translate."""
        try:
            self._window.set_status("Scanning input typing bar (F4)...")

            # Temporarily hide visual guide overlays so they don't corrupt the OCR capture
            guide_input_was_visible = False
            guide_chat_was_visible = False
            if hasattr(self._window, "_bbox_input_overlay") and self._window._bbox_input_overlay.isVisible():
                guide_input_was_visible = True
                self._window._bbox_input_overlay.hide()
            if hasattr(self._window, "_bbox_chatlog_overlay") and self._window._bbox_chatlog_overlay.isVisible():
                guide_chat_was_visible = True
                self._window._bbox_chatlog_overlay.hide()

            QApplication.processEvents()

            try:
                text = self._ocr.capture_input() if hasattr(self._ocr, "capture_input") else self._ocr.capture()
            finally:
                if guide_input_was_visible and hasattr(self._window, "_bbox_input_overlay"):
                    self._window._bbox_input_overlay.show()
                if guide_chat_was_visible and hasattr(self._window, "_bbox_chatlog_overlay"):
                    self._window._bbox_chatlog_overlay.show()

            if text and text.strip():
                clean = text.strip()
                self._window.set_input_text(clean)
                self._osd.show_translation(f"[Input F4]\n\"{clean}\"\n\nMenerjemahkan...")
                QApplication.processEvents()
                self._on_translate(clean)
            else:
                msg = (
                    "[Input F4] Tidak ada teks terdeteksi di kotak ketik.\n\n"
                    "• Pastikan chat game (tekan T) sudah terbuka & ada teks.\n"
                    "• Jika resolusi/posisi chat berbeda, gunakan tombol 'Snip Input' di RP+ Translator."
                )
                self._window.set_status("No text detected in input bar")
                self._osd.show_translation(msg)
        except Exception as e:
            err = f"OCR Input Error: {str(e)}"
            self._window.set_status(err)
            self._osd.show_translation(err)

    @pyqtSlot()
    def _on_ocr_chatlog_capture(self):
        """Capture the incoming chatlog according to snip box (F5) and translate."""
        try:
            self._window.set_status("Scanning incoming chatlog (F5)...")

            # Temporarily hide visual guide overlays
            guide_input_was_visible = False
            guide_chat_was_visible = False
            if hasattr(self._window, "_bbox_input_overlay") and self._window._bbox_input_overlay.isVisible():
                guide_input_was_visible = True
                self._window._bbox_input_overlay.hide()
            if hasattr(self._window, "_bbox_chatlog_overlay") and self._window._bbox_chatlog_overlay.isVisible():
                guide_chat_was_visible = True
                self._window._bbox_chatlog_overlay.hide()

            QApplication.processEvents()

            try:
                text = self._ocr.capture_chatlog() if hasattr(self._ocr, "capture_chatlog") else self._ocr.capture()
            finally:
                if guide_input_was_visible and hasattr(self._window, "_bbox_input_overlay"):
                    self._window._bbox_input_overlay.show()
                if guide_chat_was_visible and hasattr(self._window, "_bbox_chatlog_overlay"):
                    self._window._bbox_chatlog_overlay.show()

            if text and text.strip():
                clean = text.strip()
                self._window.set_input_text(clean)
                self._osd.show_translation(f"[Chat F5]\n\"{clean}\"\n\nMenerjemahkan...")
                QApplication.processEvents()
                self._on_translate(clean)
            else:
                msg = (
                    "[Chatlog F5] Tidak ada chat masuk terdeteksi di area snip box.\n\n"
                    "Gunakan tombol 'Snip Chat' di RP+ Translator "
                    "untuk menandai posisi area chatlog history Anda."
                )
                self._window.set_status("No text detected in chatlog snip box")
                self._osd.show_translation(msg)
        except Exception as e:
            err = f"OCR Chatlog Error: {str(e)}"
            self._window.set_status(err)
            self._osd.show_translation(err)

    @pyqtSlot()
    def _on_ocr_capture(self):
        """Legacy alias: redirects to input capture."""
        self._on_ocr_input_capture()

    # ── RP Chat Meaning (F1) ────────────────────────────

    @pyqtSlot()
    def _on_ocr_meaning_capture(self):
        """Capture incoming RP chat from chatlog and translate its meaning to Indonesian (F1)."""
        try:
            self._window.set_status("Scanning incoming RP chat (F1)...")
            self._window.set_meaning_loading()

            # Temporarily hide visual guide overlays so they don't appear in the screenshot
            guide_input_was_visible = False
            guide_chat_was_visible = False
            if hasattr(self._window, "_bbox_input_overlay") and self._window._bbox_input_overlay.isVisible():
                guide_input_was_visible = True
                self._window._bbox_input_overlay.hide()
            if hasattr(self._window, "_bbox_chatlog_overlay") and self._window._bbox_chatlog_overlay.isVisible():
                guide_chat_was_visible = True
                self._window._bbox_chatlog_overlay.hide()

            QApplication.processEvents()

            try:
                text = self._ocr.capture_chatlog() if hasattr(self._ocr, "capture_chatlog") else self._ocr.capture()
            finally:
                if guide_input_was_visible and hasattr(self._window, "_bbox_input_overlay"):
                    self._window._bbox_input_overlay.show()
                if guide_chat_was_visible and hasattr(self._window, "_bbox_chatlog_overlay"):
                    self._window._bbox_chatlog_overlay.show()

            if text and text.strip():
                clean = text.strip()
                self._window.set_meaning_loading(clean)
                self._osd.show_translation(f"[F1 - Arti RP]\n\"{clean}\"\n\nMenerjemahkan maksud roleplay...")
                QApplication.processEvents()

                # Start worker for AI meaning translation
                if hasattr(self, "_meaning_worker") and self._meaning_worker and self._meaning_worker.isRunning():
                    try:
                        self._meaning_worker.terminate()
                        self._meaning_worker.wait(500)
                    except Exception:
                        pass

                self._meaning_worker = MeaningWorker(self._translator, clean, parent=self)
                self._meaning_worker.finished.connect(self._on_meaning_done)
                self._meaning_worker.error.connect(self._on_meaning_error)
                self._meaning_worker.start()
            else:
                msg = (
                    "[F1 - Arti RP] Tidak ada chat masuk terdeteksi di area snip box.\n\n"
                    "• Pastikan ada pesan chat dari lawan main di layar Anda.\n"
                    "• Gunakan tombol 'Snip Chat' di RP+ Translator untuk menyesuaikan posisi snip box chatlog."
                )
                self._window.set_status("No chat detected for F1 meaning")
                self._window.clear_meaning()
                self._osd.show_translation(msg)
        except Exception as e:
            err = f"OCR Meaning Error: {str(e)}"
            self._window.set_status(err)
            self._osd.show_translation(err)

    @pyqtSlot(str, str)
    def _on_meaning_done(self, source_text: str, meaning_text: str):
        """Display translated Indonesian meaning on Main Window Card and OSD."""
        self._window.set_meaning_result(source_text, meaning_text)
        self._window.set_status("RP Chat meaning translated")
        osd_msg = (
            f"[Arti RP]\n{meaning_text}\n\n"
            f"[Chat Lawan]\n\"{source_text}\""
        )
        self._osd.show_translation(osd_msg)

    @pyqtSlot(str)
    def _on_meaning_error(self, error_msg: str):
        """Handle error during meaning translation."""
        self._window.set_status(f"Meaning error: {error_msg}")
        self._osd.show_translation(f"[F1 Error] {error_msg}")
        err_lower = error_msg.lower()
        if (
            "401" in error_msg
            or "unauthorized" in err_lower
            or "api key is missing" in err_lower
            or "invalid_api_key" in err_lower
            or "invalid api key" in err_lower
        ):
            self.show_api_key_dialog(is_error=True, error_detail=error_msg)

    # ── Copy Answer ─────────────────────────────────────

    @pyqtSlot(int)
    def _on_copy_answer(self, index: int):
        """Copy an answer to the clipboard with in-game OSD confirmation."""
        text = self._window.get_answer(index)
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._window.set_status(f"Option {index + 1} copied to clipboard")
            self._osd.show_translation(f"Option {index + 1} Disalin ke Clipboard:\n\"{text}\"\n\nSiap di-paste ke game (T -> Ctrl+V)")
        else:
            self._window.set_status(f"Option {index + 1} is empty")

    # ── Style ───────────────────────────────────────────

    @pyqtSlot(str)
    def _on_style_changed(self, style_name: str):
        """Handle style selection change."""
        if self._config:
            self._config.set("current_style", style_name)
            self._config.save()
        self._window.set_status(f"Style: {style_name}")

    # ── Settings ────────────────────────────────────────

    def _on_settings(self, initial_tab: int = 1):
        """Open settings dialog and apply changes."""
        settings = self._window.open_settings(
            config_manager=self._config,
            style_manager=self._styles,
            initial_tab=initial_tab,
        )
        if settings:
            self._apply_settings(settings)

    def _apply_settings(self, settings: dict):
        """Apply settings to all components."""
        if not self._config:
            return

        # Update config
        for key, value in settings.items():
            self._config.set(key, value, auto_save=False)

        # Synchronize flat and nested aliases
        if "model" in settings:
            self._config.set("ai_model", settings["model"], auto_save=False)
        if "base_url" in settings:
            self._config.set("api_base_url", settings["base_url"], auto_save=False)
        if "ocr_bbox" in settings:
            self._config.set("bbox", settings["ocr_bbox"], auto_save=False)
        if "show_ocr_bbox" in settings:
            self._config.set("show_bbox_overlay", settings["show_ocr_bbox"], auto_save=False)

        self._config.save()

        # Apply theme updates immediately
        if "theme" in settings:
            self._theme_manager.load_from_config()
            self._window.apply_theme(self._theme_manager.current_theme)
            self._osd.apply_theme(self._theme_manager.current_theme)

        # Reload components
        try:
            self._translator.reload_config()
        except (AttributeError, Exception):
            pass

        try:
            self._ocr.reload_config()
        except (AttributeError, Exception):
            pass

        try:
            self._hotkeys.reload_config()
        except (AttributeError, Exception):
            pass

        self._osd.reload_config()
        self._window.refresh_styles()
        self._window.set_status("Settings applied")

    # ── Public API ──────────────────────────────────────

    def show(self):
        """Show the main window and check for initial API key setup."""
        self._window.show()

        # Prompt for Groq API key on fresh install if not yet configured
        api_key = self._config.get("api_key", "").strip() if self._config else ""
        if not api_key:
            QTimer.singleShot(400, lambda: self.show_api_key_dialog(is_error=False))

    def get_window(self) -> MainWindow:
        """Return the main window instance."""
        return self._window

    def get_osd(self) -> OSDOverlay:
        """Return the OSD overlay instance."""
        return self._osd

    def start_hotkeys(self):
        """Start listening for global hotkeys."""
        try:
            self._hotkeys.start()
        except (AttributeError, Exception) as e:
            print(f"[AppController] Warning: Could not start hotkeys: {e}")

    def stop_hotkeys(self):
        """Stop listening for global hotkeys."""
        try:
            self._hotkeys.stop()
        except (AttributeError, Exception):
            pass
