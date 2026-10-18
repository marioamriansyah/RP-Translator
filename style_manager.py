"""
Style Manager for PRORP Translator.

Provides CRUD operations for RP translation styles and persists
changes to config automatically.
"""

from __future__ import annotations

from typing import Any


class StyleManager:
    """
    Manages RP translation styles (add / edit / delete / list).

    Each style is a dict with keys ``rule``, ``tone``, ``intensity``.
    Styles are stored inside the ``styles`` key of the application config.
    """

    def __init__(self, config_manager: Any) -> None:
        """
        Args:
            config_manager: A ConfigManager instance.
        """
        self._config = config_manager

    # ── Helpers ────────────────────────────────────────────────────────

    def _styles(self) -> dict[str, dict[str, str]]:
        """Return the mutable styles dict from config."""
        styles = self._config.get("styles")
        if styles is None:
            styles = {}
            self._config.set("styles", styles, auto_save=False)
        return styles

    def _save(self) -> None:
        """Persist the current styles to config.json."""
        self._config.save()

    # ── CRUD ───────────────────────────────────────────────────────────

    def add_style(
        self,
        name: str,
        rule: str,
        tone: str,
        intensity: str,
    ) -> None:
        """
        Add a new style.

        Args:
            name: Unique display name (e.g. "LA Street").
            rule: The translation rule / description.
            tone: Comma-separated tone descriptors.
            intensity: Intensity description.

        Raises:
            ValueError: If a style with *name* already exists.
        """
        styles = self._styles()
        if name in styles:
            raise ValueError(f"Style '{name}' already exists")

        styles[name] = {
            "rule": rule,
            "tone": tone,
            "intensity": intensity,
        }
        self._config.set("styles", styles)

    def edit_style(
        self,
        name: str,
        rule: str,
        tone: str,
        intensity: str,
    ) -> None:
        """
        Update an existing style.

        Args:
            name: The style name to update.
            rule: New rule text.
            tone: New tone text.
            intensity: New intensity text.

        Raises:
            KeyError: If the style does not exist.
        """
        styles = self._styles()
        if name not in styles:
            raise KeyError(f"Style '{name}' does not exist")

        styles[name] = {
            "rule": rule,
            "tone": tone,
            "intensity": intensity,
        }
        self._config.set("styles", styles)

    def update_style(
        self,
        old_name: str,
        new_name: str,
        rule: str,
        tone: str,
        intensity: str,
    ) -> None:
        """Update or rename an existing style."""
        styles = self._styles()
        if old_name != new_name and old_name in styles:
            del styles[old_name]

        styles[new_name] = {
            "rule": rule,
            "tone": tone,
            "intensity": intensity,
        }
        self._config.set("styles", styles)

    def delete_style(self, name: str) -> None:
        """
        Delete a style by name.

        Args:
            name: The style to remove.

        Raises:
            KeyError: If the style does not exist.
        """
        styles = self._styles()
        if name not in styles:
            raise KeyError(f"Style '{name}' does not exist")

        del styles[name]
        self._config.set("styles", styles)

    def get_style(self, name: str) -> dict[str, str]:
        """
        Retrieve a single style by name.

        Args:
            name: The style name.

        Returns:
            A dict with keys ``rule``, ``tone``, ``intensity``.

        Raises:
            KeyError: If the style does not exist.
        """
        styles = self._styles()
        if name not in styles:
            raise KeyError(f"Style '{name}' does not exist")
        return styles[name]

    def get_style_names(self) -> list[str]:
        """
        Return a sorted list of all style names.

        Returns:
            List of style name strings.
        """
        return sorted(self._styles().keys())

    def has_style(self, name: str) -> bool:
        """Check whether a style with the given name exists."""
        return name in self._styles()
