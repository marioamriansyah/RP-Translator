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





class OCREngine:
    """Wrapper around Tesseract OCR for screen-region text capture."""

    FALLBACK_TESSERACT = r"C:\Program Files (x86)\PRORP Translator\tesseract\tesseract.exe"
    FALLBACK_TESSDATA = r"C:\Program Files (x86)\PRORP Translator\tesseract\tessdata"

    def __init__(self, config_or_path: Any = None) -> None:
        """
        Args:
            config_or_path: A ConfigManager instance or a string path to tesseract.
        """
        self._config = None
        self._tesseract_path = ""

        if hasattr(config_or_path, "get"):
            self._config = config_or_path
            path = self._config.get("tesseract_path", "tesseract/tesseract.exe")
        elif isinstance(config_or_path, str):
            path = config_or_path
        else:
            path = "tesseract/tesseract.exe"

        self.set_tesseract_path(path)

    def set_tesseract_path(self, path: str) -> None:
        """Update the Tesseract executable path and set TESSDATA_PREFIX."""
        if not os.path.exists(path):
            if os.path.exists(self.FALLBACK_TESSERACT):
                path = self.FALLBACK_TESSERACT

        self._tesseract_path = path
        pytesseract.pytesseract.tesseract_cmd = path

        # Auto-configure TESSDATA_PREFIX
        candidate_tessdata = os.path.join(os.path.dirname(path), "tessdata")
        if os.path.exists(candidate_tessdata):
            os.environ["TESSDATA_PREFIX"] = candidate_tessdata
        elif os.path.exists(self.FALLBACK_TESSDATA):
            os.environ["TESSDATA_PREFIX"] = self.FALLBACK_TESSDATA

    def reload_config(self) -> None:
        """Reload configuration settings for OCR."""
        if self._config:
            path = self._config.get("tesseract_path", "tesseract/tesseract.exe")
            self.set_tesseract_path(path)

    # ── Preprocessing Pipeline ─────────────────────────────────────────

    @staticmethod
    def preprocess_image(image: Image.Image) -> list[Image.Image]:
        """
        Generate preprocessed variants of the captured image for optimal OCR:
        1. Upscaled 2.5x + Grayscale + Contrast enhanced
        2. Upscaled + Inverted (for light text on dark backgrounds, typical in GTA RP chat)
        3. Upscaled + Binarized threshold
        """
        w, h = image.size
        # Tesseract needs text characters to be ~30-35px tall for high accuracy
        scale = max(2.0, min(3.0, 100.0 / max(10, h)))
        scaled = image.resize((int(w * scale), int(h * scale)), Image.Resampling.BICUBIC)

        gray = scaled.convert("L")

        # Variant 1: Enhanced contrast
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.2)

        # Variant 2: Inverted (white text on dark background -> black text on light)
        inverted = ImageOps.invert(enhanced)

        # Variant 3: Sharpened
        sharpened = enhanced.filter(ImageFilter.SHARPEN)

        return [enhanced, inverted, sharpened]

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
    def extract_latest_chat_line(text: str) -> str:
        """
        Extracts only the newest/latest message from a multi-line chatlog (F3)
        so that older chat history is not translated.
        """
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        cleaned_lines = []
        for line in lines:
            # Strip timestamps [HH:MM:SS] or (HH:MM:SS)
            l = re.sub(r"^[\[\(]\d{1,2}:\d{2}(?::\d{2})?[\]\)]\s*", "", line)
            # Strip speaker prefix, e.g. "John_Doe says:" or "Officer_1:"
            l = re.sub(r"^(\([^\)]+\)\s*)?[A-Za-z0-9_]+(?:\s+says|\s+berkata|\s+shouts)?\s*:\s*", "", l)
            l = re.sub(r'^["\']|["\']$', "", l).strip()
            # Ignore short noise lines
            if len(l) >= 2:
                cleaned_lines.append(l)

        if cleaned_lines:
            # Return ONLY the last line (the newest incoming chat message)
            return cleaned_lines[-1]
        return text.strip()

    # ── Capture ────────────────────────────────────────────────────────

    def capture_input(self, lang: str = "ind+eng") -> str:
        """
        Capture ONLY what the user typed in the input bar (F4).
        Excludes chatlog history.
        """
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
        # Recognize using PSM 6 (single uniform block of text)
        variants = self.preprocess_image(image)
        for variant in variants[:2]:
            try:
                raw = pytesseract.image_to_string(variant, lang=lang, config="--psm 6").strip()
                cleaned = self.clean_input_text(raw)
                if cleaned and len(re.findall(r"[A-Za-z0-9]", cleaned)) >= 2:
                    return cleaned
            except Exception as e:
                print(f"[OCREngine] Input OCR error: {e}")

        # Fallback to general recognize
        raw = self.recognize(image, lang=lang)
        return self.clean_input_text(raw)

    def capture_chatlog(self, lang: str = "ind+eng") -> str:
        """
        Capture the incoming chatlog (F3) and extract ONLY the newest line,
        preventing older chat history from being translated.
        """
        bbox = {"left": 265, "top": 200, "width": 645, "height": 140}
        if self._config:
            cfg_bbox = self._config.get("chatlog_bbox")
            if cfg_bbox and isinstance(cfg_bbox, dict):
                bbox.update(cfg_bbox)

        image = self.capture_region(bbox)
        variants = self.preprocess_image(image)
        for variant in variants[:2]:
            try:
                raw = pytesseract.image_to_string(variant, lang=lang, config="--psm 6").strip()
                latest = self.extract_latest_chat_line(raw)
                if latest and len(re.findall(r"[A-Za-z0-9]", latest)) >= 2:
                    return latest
            except Exception as e:
                print(f"[OCREngine] Chatlog OCR error: {e}")

        # Fallback to general recognize
        raw = self.recognize(image, lang=lang)
        return self.extract_latest_chat_line(raw)

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
        with ImageGrab as fallback.
        """
        left = int(bbox.get("left", 0))
        top = int(bbox.get("top", 0))
        width = max(10, int(bbox.get("width", 500)))
        height = max(10, int(bbox.get("height", 100)))

        # 1. Primary: PyQt6 QScreen grabWindow (100% reliable on Windows)
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
                    pixmap = target_screen.grabWindow(0, left, top, width, height)
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
