"""
Enhanced OCR Engine for PRORP Translator.

Captures screen regions with Windows DPI awareness, applies high-precision
image preprocessing (upscaling, contrast enhancement, adaptive thresholding),
and recognizes text via Tesseract OCR (ind+eng models).
"""

import os
import re
import sys
import ctypes
from typing import Any
from pathlib import Path

import pytesseract
from PIL import ImageGrab, Image, ImageEnhance, ImageOps, ImageFilter





def find_tesseract(custom_path: str = "") -> tuple[str, str]:
    """
    Locates tesseract.exe and tessdata directory across all standard and bundled locations.
    Returns (tesseract_exe_path, tessdata_dir_path).
    """
    candidates = []

    # 1. User custom path if provided
    if custom_path:
        candidates.append(custom_path)

    # 2. Application root and _internal directories
    app_root = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(app_root, "tesseract", "tesseract.exe"))
    candidates.append(os.path.join(app_root, "tesseract.exe"))

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "tesseract", "tesseract.exe"))
        candidates.append(os.path.join(exe_dir, "_internal", "tesseract", "tesseract.exe"))
        candidates.append(os.path.join(exe_dir, "tesseract.exe"))

    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "tesseract", "tesseract.exe"))

    # 3. Standard Program Files installation paths
    candidates.extend([
        r"C:\Program Files (x86)\RP+ Translator\tesseract\tesseract.exe",
        r"C:\Program Files\RP+ Translator\tesseract\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\PRORP Translator\tesseract\tesseract.exe",
        r"C:\Program Files\PRORP Translator\tesseract\tesseract.exe",
    ])

    # 4. System PATH
    import shutil
    which_path = shutil.which("tesseract")
    if which_path:
        candidates.append(which_path)

    found_exe = ""
    for c in candidates:
        if c and os.path.exists(c) and os.path.isfile(c):
            found_exe = os.path.abspath(c)
            break

    found_tessdata = ""
    if found_exe:
        td1 = os.path.join(os.path.dirname(found_exe), "tessdata")
        if os.path.exists(td1):
            found_tessdata = td1
        else:
            for td in [
                os.path.join(app_root, "tesseract", "tessdata"),
                r"C:\Program Files (x86)\RP+ Translator\tesseract\tessdata",
                r"C:\Program Files\Tesseract-OCR\tessdata",
                r"C:\Program Files (x86)\PRORP Translator\tesseract\tessdata",
            ]:
                if os.path.exists(td):
                    found_tessdata = td
                    break

    return found_exe, found_tessdata


class OCREngine:
    """Wrapper around Tesseract OCR for screen-region text capture."""

    def __init__(self, config_or_path: Any = None) -> None:
        """
        Args:
            config_or_path: A ConfigManager instance or a string path to tesseract.
        """
        self._config = None
        self._tesseract_path = ""
        self._tessdata_path = ""

        custom = ""
        if hasattr(config_or_path, "get"):
            self._config = config_or_path
            custom = self._config.get("tesseract_path", "")
        elif isinstance(config_or_path, str):
            custom = config_or_path

        self.set_tesseract_path(custom)

    def is_available(self) -> bool:
        """Check if Tesseract binary exists and is executable."""
        return bool(self._tesseract_path and os.path.exists(self._tesseract_path))

    def set_tesseract_path(self, path: str = "") -> None:
        """Update the Tesseract executable path and set TESSDATA_PREFIX."""
        exe_path, tessdata_path = find_tesseract(path)
        self._tesseract_path = exe_path
        self._tessdata_path = tessdata_path

        if exe_path:
            pytesseract.pytesseract.tesseract_cmd = exe_path
            if tessdata_path:
                os.environ["TESSDATA_PREFIX"] = tessdata_path
        else:
            pytesseract.pytesseract.tesseract_cmd = path or "tesseract.exe"

    def reload_config(self) -> None:
        """Reload configuration settings for OCR."""
        if self._config:
            path = self._config.get("tesseract_path", "")
            self.set_tesseract_path(path)

    # ── Preprocessing Pipeline ─────────────────────────────────────────

    @staticmethod
    def preprocess_image(image: Image.Image) -> list[Image.Image]:
        """
        Generate preprocessed variants of the captured image for optimal OCR:
        1. Inverted (black text on white, Tesseract's optimal format for GTA white chat)
        2. High-contrast thresholded / binarized
        3. Enhanced grayscale with autocontrast
        4. Sharpened inverted
        """
        w, h = image.size
        # Tesseract needs text characters to be ~35-40px tall for high accuracy
        scale = max(2.5, min(4.0, 120.0 / max(10, h)))
        scaled = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        gray = scaled.convert("L")
        auto_contrasted = ImageOps.autocontrast(gray, cutoff=2)

        # Variant 1: Inverted (white text on dark background -> black text on light)
        inverted = ImageOps.invert(auto_contrasted)

        # Variant 2: Binary threshold (isolates white/colored GTA text from scenery)
        # Threshold at pixel level 130
        table = [0 if i < 130 else 255 for i in range(256)]
        binary = gray.point(table, "1").convert("L")
        binary_inverted = ImageOps.invert(binary)

        # Variant 3: Sharpened inverted
        sharpened = inverted.filter(ImageFilter.SHARPEN)

        return [inverted, binary_inverted, auto_contrasted, sharpened]

    # ── Text Cleaning & RP Chat Normalization ──────────────────────────

    @staticmethod
    def clean_rp_chat(text: str) -> str:
        """
        Cleans common GTA RP chat artifacts from OCR output:
        - Timestamps like [18:32:05] or (21:10)
        - Speaker tags like 'Officer_Johnson: ' or 'Warga_01 says: '
        - Unnecessary quotes and extra whitespace
        """
        if not text:
            return ""

        # Normalize line breaks
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        cleaned_lines = []
        for line in lines:
            # Strip timestamps [HH:MM:SS] or (HH:MM:SS) or (HH:MM)
            l = re.sub(r"^[\[\(]\d{1,2}:\d{2}(?::\d{2})?[\]\)]\s*", "", line)

            # Strip common speaker prefixes, e.g. "Name_Surname:" or "Name says:" or "(Radio) Name:"
            l = re.sub(r"^(\([^\)]+\)\s*)?[A-Za-z0-9_]+(?:\s+says|\s+berkata|\s+shouts)?\s*:\s*", "", l)

            # Strip leading/trailing quotation marks
            l = re.sub(r'^["\']|["\']$', "", l).strip()

            if l:
                cleaned_lines.append(l)

        if cleaned_lines:
            return " ".join(cleaned_lines)
        return text.strip()

    @staticmethod
    def clean_input_text(text: str) -> str:
        """
        Cleans what the player types in the chat input bar (F4):
        - Removes blinking cursor artifacts ('|', '_', 'I', ']', '>', '~')
        - Removes leading command prompt symbols (': ', '> ')
        - Normalizes whitespace
        """
        if not text:
            return ""
        # Join any fragmented lines since typing bar is single-line
        t = " ".join([l.strip() for l in text.splitlines() if l.strip()])
        # Remove trailing blinking cursor artifacts commonly caught by OCR
        t = re.sub(r"[\s\|\_\[\]\>\~\{\}\\\/]+$", "", t).strip()
        # Remove leading prompts e.g. "Say: ", "> ", ": "
        t = re.sub(r"^(?:say|katakan|chat)?\s*[:\>]\s*", "", t, flags=re.IGNORECASE).strip()
        # Clean quotes
        t = re.sub(r'^["\']|["\']$', "", t).strip()
        return t

    @staticmethod
    def clean_chatlog_text(text: str) -> str:
        """
        Cleans OCR output from chatlog snip box while PRESERVING ALL LINES
        inside the snip box so the translation matches the entire selected area.
        - Strips timestamps like [18:32:05] or (21:10) from line starts
        - Strips noise characters
        - Joins wrapped lines into full coherent dialogue
        """
        if not text:
            return ""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        cleaned_lines = []
        for line in lines:
            # Strip timestamps [HH:MM:SS] or (HH:MM:SS) or (HH:MM)
            l = re.sub(r"^[\[\(]\d{1,2}:\d{2}(?::\d{2})?[\]\)]\s*", "", line)
            # Strip outer quotation marks
            l = re.sub(r'^["\']|["\']$', "", l).strip()
            # Ignore single stray noise characters like '_', '|', '~', '-'
            if len(l) >= 2 or (len(l) == 1 and l.isalnum()):
                cleaned_lines.append(l)

        if cleaned_lines:
            return " ".join(cleaned_lines)
        return text.strip()

    @staticmethod
    def extract_latest_chat_line(text: str) -> str:
        """Alias to clean_chatlog_text for backward compatibility."""
        return OCREngine.clean_chatlog_text(text)

    # ── Capture ────────────────────────────────────────────────────────

    def capture_input(self, lang: str = "ind+eng") -> str:
        """
        Capture ONLY what the user typed in the input bar (F4).
        Excludes chatlog history.
        """
        if not self.is_available():
            raise FileNotFoundError(
                "Mesin OCR Tesseract tidak ditemukan.\n"
                "Pastikan folder tesseract terpasang atau periksa Settings > OCR."
            )

        bbox = {"left": 265, "top": 350, "width": 645, "height": 45}
        if self._config:
            cfg_bbox = (
                self._config.get("input_bbox")
                or self._config.get("bbox")
                or self._config.get("ocr_bbox")
            )
            if cfg_bbox and isinstance(cfg_bbox, dict):
                bbox.update(cfg_bbox)

        image = self.capture_region(bbox)
        variants = self.preprocess_image(image)

        # For single-line typing input bar:
        # PSM 7 = Treat image as a single text line (Highest accuracy for GTA chat typing box)
        # PSM 6 = Single uniform block
        # PSM 11 = Sparse text
        for psm in ["--psm 7", "--psm 6", "--psm 11"]:
            for variant in variants:
                try:
                    raw = pytesseract.image_to_string(variant, lang=lang, config=psm).strip()
                    cleaned = self.clean_input_text(raw)
                    if cleaned and len(re.findall(r"[A-Za-z0-9]", cleaned)) >= 2:
                        return cleaned
                except Exception as e:
                    print(f"[OCREngine] Input OCR error ({psm}): {e}")

        # Fallback to general multi-pass recognize
        raw = self.recognize(image, lang=lang)
        return self.clean_input_text(raw)

    def capture_chatlog(self, lang: str = "ind+eng") -> str:
        """
        Capture the incoming chatlog according to the configured snip box (chatlog_bbox).
        Reads ALL text inside the snip box so the translation matches the user's selection.
        """
        if not self.is_available():
            raise FileNotFoundError(
                "Mesin OCR Tesseract tidak ditemukan.\n"
                "Pastikan folder tesseract terpasang atau periksa Settings > OCR."
            )

        bbox = {"left": 265, "top": 200, "width": 645, "height": 140}
        if self._config:
            cfg_bbox = self._config.get("chatlog_bbox")
            if cfg_bbox and isinstance(cfg_bbox, dict):
                bbox.update(cfg_bbox)

        image = self.capture_region(bbox)
        variants = self.preprocess_image(image)

        # Multi-line chat history modes
        best_candidate = ""
        for psm in ["--psm 6", "--psm 4", "--psm 11", "--psm 3"]:
            for variant in variants:
                try:
                    raw = pytesseract.image_to_string(variant, lang=lang, config=psm).strip()
                    cleaned = self.clean_chatlog_text(raw)
                    if cleaned and len(re.findall(r"[A-Za-z0-9]", cleaned)) >= 2:
                        if len(cleaned) > len(best_candidate):
                            best_candidate = cleaned
                            if len(re.findall(r"[A-Za-z0-9]", best_candidate)) >= 6:
                                return best_candidate
                except Exception as e:
                    print(f"[OCREngine] Chatlog OCR error ({psm}): {e}")

        if best_candidate:
            return best_candidate

        # Fallback to general recognize
        raw = self.recognize(image, lang=lang)
        return self.clean_chatlog_text(raw)

    def capture(self, lang: str = "ind+eng") -> str:
        """
        Default capture: captures input typing bar.
        Called by hotkeys and UI.
        """
        return self.capture_input(lang=lang)

    @staticmethod
    def capture_region(bbox: dict[str, int]) -> Image.Image:
        """
        Take a screenshot of a screen region defined by *bbox*.
        Uses PyQt6 QScreen grabWindow for robust Windows DirectX and High-DPI support,
        with multi-monitor geometry compensation and ImageGrab fallback.
        """
        left = int(bbox.get("left", 0))
        top = int(bbox.get("top", 0))
        width = max(10, int(bbox.get("width", 500)))
        height = max(10, int(bbox.get("height", 100)))

        # 1. Primary: PyQt6 QScreen grabWindow
        try:
            from PyQt6.QtGui import QGuiApplication, QImage
            app = QGuiApplication.instance()
            if app:
                target_screen = QGuiApplication.primaryScreen()
                for screen in QGuiApplication.screens():
                    if screen.geometry().contains(left, top):
                        target_screen = screen
                        break

                if target_screen:
                    # In Qt, grabWindow(0, x, y, w, h) coordinates are relative
                    # to the screen's own coordinate origin.
                    local_x = left - target_screen.geometry().x()
                    local_y = top - target_screen.geometry().y()
                    pixmap = target_screen.grabWindow(0, local_x, local_y, width, height)
                    if not pixmap.isNull():
                        qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                        w = qimg.width()
                        h = qimg.height()
                        ptr = qimg.bits()
                        ptr.setsize(h * w * 4)
                        return Image.frombuffer("RGBA", (w, h), bytes(ptr), "raw", "RGBA", 0, 1).convert("RGB")
        except Exception as e:
            print(f"[OCREngine] Qt screen grab notice: {e}")

        # 2. Fallback: Pillow ImageGrab
        right = left + width
        bottom = top + height
        try:
            return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True).convert("RGB")
        except Exception:
            return ImageGrab.grab(bbox=(left, top, right, bottom)).convert("RGB")

    # ── Recognition ────────────────────────────────────────────────────

    def recognize(self, image: Image.Image, lang: str = "ind+eng") -> str:
        """
        Run multi-pass OCR on a PIL Image with image preprocessing.
        Tries enhanced contrast first; if confidence is low, tries inverted.
        """
        variants = self.preprocess_image(image)

        # Primary PSM modes to try:
        # PSM 6 = Assume a single uniform block of text
        # PSM 11 = Sparse text. Find as much text as possible in no particular order
        configs = ["--psm 6", "--psm 11", "--psm 3"]

        best_text = ""

        # Pass 1: Try enhanced and inverted with PSM 6
        for variant in variants[:2]:
            try:
                raw = pytesseract.image_to_string(variant, lang=lang, config=configs[0]).strip()
                cleaned = self.clean_rp_chat(raw)
                if cleaned and len(cleaned) > len(best_text):
                    best_text = cleaned
                    # If we found solid alphanumeric text, stop early
                    if len(re.findall(r"[A-Za-z0-9]", best_text)) >= 3:
                        return best_text
            except Exception as e:
                print(f"[OCREngine] OCR pass error: {e}")

        # Pass 2: Fallback configs if best_text is still empty
        if not best_text:
            for cfg in configs[1:]:
                for variant in variants:
                    try:
                        raw = pytesseract.image_to_string(variant, lang=lang, config=cfg).strip()
                        cleaned = self.clean_rp_chat(raw)
                        if cleaned:
                            return cleaned
                    except Exception:
                        pass

        return best_text

    # ── Convenience ────────────────────────────────────────────────────

    def capture_and_recognize(
        self,
        bbox: dict[str, int],
        lang: str = "ind+eng",
    ) -> str:
        """Capture screen region and recognise text with cleaning."""
        image = self.capture_region(bbox)
        return self.recognize(image, lang=lang)

    def capture_debug(self, bbox: dict[str, int], lang: str = "ind+eng") -> dict[str, Any]:
        """
        Detailed capture diagnostic returning raw capture, preprocessed variants,
        and recognized text for live preview in Settings.
        """
        image = self.capture_region(bbox)
        variants = self.preprocess_image(image)
        raw_text = ""
        try:
            raw_text = pytesseract.image_to_string(variants[0], lang=lang, config="--psm 6").strip()
        except Exception as e:
            raw_text = f"Error: {e}"

        cleaned_text = self.clean_rp_chat(raw_text)

        return {
            "raw_image": image,
            "processed_image": variants[0],
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "bbox": bbox,
            "tesseract_path": self._tesseract_path,
        }
