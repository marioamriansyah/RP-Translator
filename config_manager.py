"""
Config Manager for PRORP Translator.

Handles loading, saving, and accessing application configuration
stored in config.json. Auto-saves on any change.
"""

import json
import os
from pathlib import Path
from typing import Any


# Default configuration matching the expected structure
DEFAULT_CONFIG: dict[str, Any] = {
    "ai_model": "qwen/qwen3.8-27b",
    "api_key": "",
    "api_base_url": "https://api.groq.com/openai/v1",
    "bbox": {"height": 53, "left": 11, "top": 557, "width": 671},
    "input_bbox": {"height": 53, "left": 11, "top": 557, "width": 671},
    "chatlog_bbox": {"height": 136, "left": 15, "top": 420, "width": 664},
    "eula_accepted": True,
    "hotkey_ans1": "<ctrl>+1",
    "hotkey_ans2": "<ctrl>+2",
    "hotkey_ans3": "<ctrl>+3",
    "hotkey_clipboard": "<f5>",
    "hotkey_ocr": "<f4>",
    "hotkey_ocr_input": "<f4>",
    "hotkey_ocr_chatlog": "<f3>",
    "hotkey_scroll_down": "<page_down>",
    "hotkey_scroll_up": "<page_up>",
    "hotkey_toggle_window": "<insert>",
    "last_style": "LA Street",
    "osd_bbox": {"height": 220, "left": 11, "top": 620, "width": 671},
    "osd_duration": 12,
    "osd_enabled": True,
    "osd_font_color": "#a6e3a1",
    "osd_font_size": 12,
    "show_bbox_overlay": True,
    "smart_reply_enabled": True,
    "styles": {
        "American Formal": {
            "intensity": "natural and moderate",
            "rule": "Natural contemporary American English suitable for everyday GTA RP dialogue.",
            "tone": "casual, natural, straightforward, conversational",
        },
        "British Formal": {
            "intensity": "none",
            "rule": "Formal and polite British English.",
            "tone": "formal, polite, respectful",
        },
        "Cartel Mexico": {
            "intensity": "moderate",
            "rule": "Mexican Cartel RP English with slight Spanish influence.",
            "tone": "aggressive, commanding, slightly accented",
        },
        "LA Street": {
            "intensity": "light to moderate street influence",
            "rule": "Contemporary informal Los Angeles street-style American English with a subtle street influence.",
            "tone": "casual, confident, relaxed, street-aware",
        },
        "Mafia Italy": {
            "intensity": "moderate",
            "rule": "Italian Mafia RP English, New York/Chicago mob style.",
            "tone": "confident, slightly aggressive, mob-style",
        },
    },
    "tesseract_path": "tesseract/tesseract.exe",
}


class ConfigManager:
    """Manages application configuration with auto-save on change."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """
        Initialize the config manager.

        Args:
            config_path: Path to config.json. Defaults to config.json
                         in the same directory as this module.
        """
        if config_path is None:
            base_dir = Path(__file__).parent
            self._config_path = base_dir / "config.json"
        else:
            self._config_path = Path(config_path)

        self._config: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from disk, merging with defaults for any missing keys."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Deep-merge defaults with loaded config (loaded takes priority)
                self._config = self._deep_merge(DEFAULT_CONFIG, loaded)
            except (json.JSONDecodeError, OSError) as e:
                print(f"[ConfigManager] Error loading config, using defaults: {e}")
                self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            # No config file yet — start with defaults and persist them
            self._config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()

    @property
    def config(self) -> dict[str, Any]:
        """Return the raw configuration dict."""
        return self._config

    def save(self) -> None:
        """Persist current configuration to disk."""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[ConfigManager] Error saving config: {e}")

    # ── Getters / Setters ──────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: The configuration key.
            default: Fallback value if key is missing.

        Returns:
            The configuration value, or *default* if not found.
        """
        val = self._config.get(key)
        if val is not None:
            return val
        return default

    def set(self, key: str, value: Any, *, auto_save: bool = True) -> None:
        """
        Set a configuration value and optionally auto-save.

        Args:
            key: The configuration key.
            value: The new value.
            auto_save: Whether to persist to disk immediately (default True).
        """
        self._config[key] = value
        if auto_save:
            self.save()

    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Get a nested configuration value using a sequence of keys.

        Example:
            ``config.get_nested("bbox", "width")``

        Args:
            *keys: Chain of dict keys to traverse.
            default: Fallback if any key is missing.

        Returns:
            The nested value, or *default*.
        """
        current: Any = self._config
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            else:
                return default
        return current

    def set_nested(self, *keys: str, value: Any, auto_save: bool = True) -> None:
        """
        Set a nested configuration value.

        Example:
            ``config.set_nested("bbox", "width", value=800)``

        Args:
            *keys: Chain of dict keys to traverse. The last key is set to *value*.
            value: The new value.
            auto_save: Whether to persist to disk immediately.
        """
        if not keys:
            return
        current = self._config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value
        if auto_save:
            self.save()

    @property
    def data(self) -> dict[str, Any]:
        """Return the full configuration dictionary (read-only reference)."""
        return self._config

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """
        Recursively merge *override* into a copy of *base*.

        Values in *override* take priority. Nested dicts are merged recursively;
        all other types are replaced wholesale.
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def reset_to_defaults(self) -> None:
        """Reset all configuration to built-in defaults and save."""
        self._config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.save()
