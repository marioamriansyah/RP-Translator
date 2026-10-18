"""
Apple Liquid Glass Style Editor Dialog - Edit or create RP translation styles.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton,
)
from PyQt6.QtCore import Qt
from ui.vector_icons import get_vector_icon


STYLE_EDITOR_STYLESHEET = """
QDialog {
    background-color: #08090A;
    color: #F7F8F8;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 9.5pt;
}

QLabel {
    color: #D0D6E0;
    font-size: 9pt;
    font-weight: 600;
}

QLineEdit, QTextEdit {
    background-color: #0D0E10;
    color: #F7F8F8;
    border: 1px solid #222326;
    border-radius: 6px;
    padding: 8px;
    font-size: 9pt;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #5E6AD2;
}

QPushButton {
    background-color: #121417;
    color: #8A8F98;
    border: 1px solid #222326;
    border-radius: 9999px;
    padding: 7px 16px;
    font-size: 9pt;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F7F8F8;
    border-color: #3E4048;
}
"""


class StyleEditorDialog(QDialog):
    """Dialog for editing or creating an RP translation style."""

    def __init__(self, style_data: dict = None, parent=None):
        super().__init__(parent)
        self._style_data = style_data or {}
        self._is_editing = bool(style_data)

        self.setWindowTitle("Edit RP Style" if self._is_editing else "New RP Style")
        self.resize(440, 360)
        self.setStyleSheet(STYLE_EDITOR_STYLESHEET)

        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g. South Central Hood")
        form.addRow("Style Name:", self._name_input)

        self._rule_input = QTextEdit()
        self._rule_input.setPlaceholderText("Describe how sentences should be translated...")
        self._rule_input.setMaximumHeight(90)
        form.addRow("Rule / Prompt:", self._rule_input)

        self._tone_input = QLineEdit()
        self._tone_input.setPlaceholderText("e.g. aggressive, street-smart, fast-paced")
        form.addRow("Tone:", self._tone_input)

        self._intensity_input = QLineEdit()
        self._intensity_input.setPlaceholderText("e.g. heavy slang, moderate, subtle")
        form.addRow("Intensity:", self._intensity_input)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save Style")
        save_btn.setIcon(get_vector_icon("save", color="#08090A", size=14))
        save_btn.setStyleSheet(
            "QPushButton { background-color: #E5E5E6; color: #08090A; font-weight: 600; padding: 7px 22px; border-radius: 9999px; }"
            "QPushButton:hover { background-color: #F7F8F8; }"
        )
        save_btn.clicked.connect(self._on_save)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)

    def _populate_fields(self):
        if self._style_data:
            self._name_input.setText(self._style_data.get("name", ""))
            self._rule_input.setPlainText(self._style_data.get("rule", ""))
            self._tone_input.setText(self._style_data.get("tone", ""))
            self._intensity_input.setText(str(self._style_data.get("intensity", "")))

    def _on_save(self):
        name = self._name_input.text().strip()
        rule = self._rule_input.toPlainText().strip()
        if not name or not rule:
            return
        self.accept()

    def get_style_data(self) -> dict:
        return {
            "name": self._name_input.text().strip(),
            "rule": self._rule_input.toPlainText().strip(),
            "tone": self._tone_input.text().strip() or "natural",
            "intensity": self._intensity_input.text().strip() or "moderate",
        }
