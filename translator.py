"""
Translation Engine for PRORP Translator.

Handles slang library lookups and AI-powered translation via the
Groq API (OpenAI-compatible chat completions endpoint).
"""

import json
import re
from pathlib import Path
from typing import Any

import httpx


class Translator:
    """
    Translates Indonesian text to styled English for GTA RP.

    Translation flow:
    1. Check slang_library.json for an exact match under the chosen style.
    2. If found → return the 3 pre-defined variants instantly.
    3. If not found → call the Groq AI API for 3 styled translations.
    """

    def __init__(
        self,
        config_manager: Any,
        slang_path: str | Path | None = None,
    ) -> None:
        """
        Args:
            config_manager: A ConfigManager instance for API settings & styles.
            slang_path: Path to slang_library.json. Defaults to
                        slang_library.json beside this module.
        """
        self._config = config_manager

        if slang_path is None:
            slang_path = Path(__file__).parent / "slang_library.json"
        else:
            slang_path = Path(slang_path)

        self._slang_path = slang_path
        self._ignore_words: list[str] = []
        # Structure: { style_name_lower: { phrase_lower: [ans1, ans2, ans3] } }
        self._styles_slang: dict[str, dict[str, list[str]]] = {}
        self._load_slang_library(self._slang_path)

    # ── Slang Library ──────────────────────────────────────────────────

    def _load_slang_library(self, path: Path) -> None:
        """
        Load the slang library from disk.

        Structure in slang_library.json:
        {
            "ignore_words": ["Los Santos", ...],
            "styles": {
                "American Formal": {
                    "halo": {"1": "Hello.", "2": "Hi there.", "3": "Greetings."},
                    ...
                }
            }
        }
        """
        if not path.exists():
            print(f"[Translator] Slang library not found at {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data: dict = json.load(f)

            self._ignore_words = data.get("ignore_words", [])

            styles_data = data.get("styles", {})
            self._styles_slang = {}

            for style_name, phrases in styles_data.items():
                s_key = style_name.strip().lower()
                self._styles_slang[s_key] = {}

                for phrase, answers in phrases.items():
                    p_key = phrase.strip().lower()
                    if isinstance(answers, dict):
                        # {"1": "...", "2": "...", "3": "..."}
                        v1 = answers.get("1", "")
                        v2 = answers.get("2", v1)
                        v3 = answers.get("3", v2)
                        self._styles_slang[s_key][p_key] = [v1, v2, v3]
                    elif isinstance(answers, list):
                        padded = answers + [""] * (3 - len(answers))
                        self._styles_slang[s_key][p_key] = padded[:3]

            total_entries = sum(len(v) for v in self._styles_slang.values())
            print(f"[Translator] Loaded {len(self._styles_slang)} styles with {total_entries} phrases from slang library")
        except Exception as e:
            print(f"[Translator] Error loading slang library: {e}")

    def check_slang_library(self, text: str, style_name: str) -> list[str] | None:
        """Alias for lookup_slang."""
        return self.lookup_slang(text, style_name)

    def lookup_slang(self, text: str, style_name: str) -> list[str] | None:
        """
        Look up Indonesian text in the slang library for the given style.

        Args:
            text: Indonesian input text.
            style_name: The RP style name (e.g. "LA Street").

        Returns:
            A list of 3 variant strings if an exact match is found,
            otherwise None.
        """
        key = text.strip().lower()
        if not key:
            return None

        # Clean punctuation from the lookup query for matching flexibility
        clean_key = re.sub(r"[!?,.]+$", "", key).strip()

        # Find the matching style
        style_key = style_name.strip().lower()
        style_phrases = self._styles_slang.get(style_key)

        if not style_phrases:
            # Fallback: check if any style contains the key
            for s_name, s_dict in self._styles_slang.items():
                if style_key in s_name or s_name in style_key:
                    style_phrases = s_dict
                    break

        if style_phrases:
            # Exact match with original text
            if key in style_phrases:
                return style_phrases[key]
            # Match without trailing punctuation
            if clean_key in style_phrases:
                return style_phrases[clean_key]

        return None

    # ── AI Translation ─────────────────────────────────────────────────

    def translate(
        self,
        text: str,
        style_name: str,
        ignore_words: list[str] | None = None,
    ) -> list[str]:
        """
        Synchronous translation for thread execution.

        First checks the slang library; falls back to the Groq AI API.
        """
        text = text.strip()
        if not text:
            return ["", "", ""]

        # 1. Slang library lookup
        slang_result = self.lookup_slang(text, style_name)
        if slang_result is not None:
            return slang_result

        # 2. AI translation via Groq API
        effective_ignore = list(self._ignore_words)
        if ignore_words:
            effective_ignore.extend(ignore_words)

        # Also merge ignore_words from config
        cfg_ignore = self._config.get("ignore_words", [])
        if cfg_ignore and isinstance(cfg_ignore, list):
            effective_ignore.extend(cfg_ignore)

        return self._translate_with_ai(text, style_name, list(set(effective_ignore)))

    def _translate_with_ai(
        self,
        text: str,
        style_name: str,
        ignore_words: list[str],
    ) -> list[str]:
        """Call the Groq API (or compatible endpoint) synchronously."""
        styles: dict = self._config.get("styles", {})
        style = styles.get(style_name, {})

        rule = style.get("rule", "Natural contemporary American English suitable for GTA RP dialogue.")
        tone = style.get("tone", "casual, natural, straightforward, conversational")
        intensity = style.get("intensity", "moderate")

        ignore_str = ", ".join(ignore_words) if ignore_words else "none"

        system_prompt = (
            "You are a GTA RP translator. Translate the following Indonesian text to English.\n"
            f"Style: {style_name}\n"
            f"Rule: {rule}\n"
            f"Tone: {tone}\n"
            f"Intensity: {intensity}\n"
            "\n"
            f"Ignore words (keep as-is): {ignore_str}\n"
            "\n"
            "Provide exactly 3 different English translations, numbered 1-3.\n"
            "Each should match the style while conveying the same meaning.\n"
            "Format: just the 3 lines, numbered."
        )

        api_key = self._config.get("api_key", "")
        api_base = self._config.get("api_base_url") or self._config.get("base_url", "https://api.groq.com/openai/v1")
        model = self._config.get("ai_model") or self._config.get("model", "qwen/qwen3.8-27b")

        if not api_key:
            raise ValueError("API Key is missing. Please set your Groq API key in Settings.")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = f"{api_base.rstrip('/')}/chat/completions"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No response received from AI model.")

        content = choices[0]["message"]["content"]
        return self._parse_response(content)

    @staticmethod
    def _parse_response(content: str) -> list[str]:
        """
        Parse the AI response into exactly 3 translation strings.
        """
        lines = [line.strip() for line in content.strip().splitlines() if line.strip()]

        results: list[str] = []
        for line in lines:
            # Strip leading numbering: "1. ", "1) ", "1: ", etc.
            cleaned = re.sub(r"^\d+[\.\)\:\-]\s*", "", line).strip()
            # Strip quotes if enclosed
            cleaned = re.sub(r'^["\']|["\']$', '', cleaned).strip()
            if cleaned:
                results.append(cleaned)

        while len(results) < 3:
            results.append(results[-1] if results else "")
        return results[:3]

    def translate_to_indonesian(self, text: str) -> str:
        """
        Translate English GTA RP chatlog / slang dialogue into natural Indonesian
        so the player understands the roleplay meaning and nuance (Hotkey F1).
        """
        text = text.strip()
        if not text:
            return ""

        api_key = self._config.get("api_key", "")
        api_base = self._config.get("api_base_url") or self._config.get("base_url", "https://api.groq.com/openai/v1")
        model = self._config.get("ai_model") or self._config.get("model", "qwen/qwen3.8-27b")

        if not api_key:
            raise ValueError("API Key is missing. Please set your Groq API key in Settings.")

        system_prompt = (
            "You are an expert GTA RP (Grand Theft Auto Roleplay) assistant.\n"
            "Your task is to translate and explain English in-game roleplay chat/dialogue into clear, natural, and accurate Bahasa Indonesia.\n"
            "Ensure American/gang/mob/police/street RP slangs and idioms (e.g. 'pack', 'heat', 'cuff', 'ops', 'cuh', 'bogus', '10-4', 'lay low') "
            "are interpreted correctly according to GTA RP context so the player understands the exact intention of the other player.\n"
            "Output ONLY the Indonesian translation / meaning directly, in 1-2 concise and natural sentences. Do not include notes, quotes, or conversational preamble."
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.4,
            "max_tokens": 256,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = f"{api_base.rstrip('/')}/chat/completions"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No response received from AI model.")

        content = choices[0]["message"]["content"].strip()
        content = re.sub(r'^["\']|["\']$', '', content).strip()
        return content

    def reload_config(self) -> None:
        """Reload configuration and refresh slang library."""
        self._load_slang_library(self._slang_path)
