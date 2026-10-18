"""
Groq API Key Dialog - Modern modal dialog for setting or updating the Groq API key.

Supports both:
1. First-time setup on fresh install (when API key is empty)
2. Recovery popup when translation encounters '401 Unauthorized' (expired/invalid key)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QApplication, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices, QColor, QFont

from ui.vector_icons import get_vector_icon, get_app_qicon, create_app_icon, create_rp_plus_logo
from ui.theme_manager import ThemeManager, _is_light_color


class ApiKeyDialog(QDialog):
    """Modern modal dialog prompting the user to configure their Groq API Key."""

    api_key_saved = pyqtSignal(str)

    def __init__(self, config_manager=None, is_error: bool = False, error_detail: str = "", parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._is_error = is_error
        self._error_detail = error_detail
        self._show_key = False

        self.setWindowTitle("Groq API Key Setup" if not is_error else "Groq API Key Error (401)")
        self.setWindowIcon(get_app_qicon())
        self.setFixedWidth(500)
        self.setModal(True)

        self._setup_ui()
        self._load_current_key()

    def _setup_ui(self):
        tm = ThemeManager.get_instance(self._config)
        t = tm.current_theme
        acc1 = t.accent_1 if t else "#5E6AD2"
        acc2 = t.accent_2 if t else "#F91880"
        bg_col = "#141517"
        border_col = "#28292C"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_col};
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }}
            QLabel {{
                color: #FFFFFF;
                font-family: 'Segoe UI', -apple-system, sans-serif;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # ── 1. Header Row (App Logo + Title) ───────────────────
        header = QHBoxLayout()
        header.setSpacing(12)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(create_app_icon(34))
        header.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        main_title = QLabel("Groq API Key" if not self._is_error else "Groq API Key - 401 Unauthorized")
        main_title.setStyleSheet("font-size: 13pt; font-weight: 700; color: #FFFFFF;")
        title_box.addWidget(main_title)

        sub_title = QLabel(
            "Diperlukan untuk menghubungkan terjemahan AI RP+"
            if not self._is_error
            else "API Key tidak valid atau telah kadaluarsa"
        )
        sub_title.setStyleSheet("font-size: 8.5pt; color: #8A8D98;")
        title_box.addWidget(sub_title)

        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # ── 2. Status Alert / Notice Banner ────────────────────
        banner = QFrame()
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        banner_layout.setSpacing(4)

        if self._is_error:
            banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 69, 58, 0.12);
                    border: 1px solid rgba(255, 69, 58, 0.35);
                    border-radius: 8px;
                }
            """)
            err_title = QLabel("Kunci API Tidak Valid / Kadaluarsa (401)")
            err_title.setStyleSheet("font-size: 9pt; font-weight: 700; color: #FF453A;")
            banner_layout.addWidget(err_title)

            err_desc = QLabel(
                "Permintaan terjemahan AI gagal karena Groq menolak kunci saat ini. "
                "Silakan masukkan Groq API Key baru yang aktif di bawah ini."
            )
            err_desc.setStyleSheet("font-size: 8pt; color: #E5E5EA;")
            err_desc.setWordWrap(True)
            banner_layout.addWidget(err_desc)
        else:
            banner.setStyleSheet("""
                QFrame {
                    background-color: rgba(94, 106, 210, 0.12);
                    border: 1px solid rgba(94, 106, 210, 0.35);
                    border-radius: 8px;
                }
            """)
            welcome_title = QLabel("Aktivasi Terjemahan AI")
            welcome_title.setStyleSheet(f"font-size: 9pt; font-weight: 700; color: {acc1};")
            banner_layout.addWidget(welcome_title)

            welcome_desc = QLabel(
                "Selamat datang di RP+ Translator! Masukkan Groq API Key Anda untuk mulai menerjemahkan "
                "di dalam game. Groq API 100% Gratis dan memiliki respon ultra-cepat."
            )
            welcome_desc.setStyleSheet("font-size: 8pt; color: #D0D3DC;")
            welcome_desc.setWordWrap(True)
            banner_layout.addWidget(welcome_desc)

        layout.addWidget(banner)

        # ── 3. Step-by-Step Instructions + Console Link ────────
        guide_box = QFrame()
        guide_box.setStyleSheet("""
            QFrame {
                background-color: #191B1E;
                border: 1px solid #282A2E;
                border-radius: 8px;
            }
        """)
        guide_layout = QVBoxLayout(guide_box)
        guide_layout.setContentsMargins(14, 10, 14, 10)
        guide_layout.setSpacing(6)

        guide_hdr = QLabel("Cara Mendapatkan API Key (Gratis 1 Menit):")
        guide_hdr.setStyleSheet("font-size: 8.5pt; font-weight: 700; color: #FFFFFF;")
        guide_layout.addWidget(guide_hdr)

        steps_text = QLabel(
            "1. Klik tombol di bawah untuk membuka Groq Console\n"
            "2. Login / Buat akun gratis (Google / GitHub)\n"
            "3. Klik 'Create API Key', beri nama bebas, lalu salin kuncinya"
        )
        steps_text.setStyleSheet("font-size: 8pt; color: #A0A3AD; line-height: 1.4;")
        guide_layout.addWidget(steps_text)

        link_btn = QPushButton("Buka Groq Console (console.groq.com/keys)")
        link_btn.setIcon(get_vector_icon("external_link", color="#FFFFFF", size=13))
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #24262B;
                color: #FFFFFF;
                border: 1px solid #33363D;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 8.5pt;
                font-weight: 600;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #2D3037;
                border-color: {acc1};
            }}
        """)
        link_btn.clicked.connect(self._open_groq_console)
        guide_layout.addWidget(link_btn)

        layout.addWidget(guide_box)

        # ── 4. API Key Input Card ──────────────────────────────
        input_container = QVBoxLayout()
        input_container.setSpacing(6)

        input_label = QLabel("Masukkan Groq API Key:")
        input_label.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #A0A3AD;")
        input_container.addWidget(input_label)

        input_box = QFrame()
        input_box.setStyleSheet("""
            QFrame {
                background-color: #121315;
                border: 1px solid #2B2C30;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #5E6AD2;
            }
        """)
        input_box_layout = QHBoxLayout(input_box)
        input_box_layout.setContentsMargins(10, 4, 6, 4)
        input_box_layout.setSpacing(6)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("gsk_...")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 9.5pt;
                padding: 4px 0;
            }
        """)
        self._key_input.returnPressed.connect(self._on_save_clicked)
        input_box_layout.addWidget(self._key_input, stretch=1)

        # Toggle Show / Hide Password
        self._toggle_eye_btn = QPushButton()
        self._toggle_eye_btn.setIcon(get_vector_icon("eye", color="#8A8D98", size=14))
        self._toggle_eye_btn.setToolTip("Lihat / Sembunyikan API Key")
        self._toggle_eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_eye_btn.setFixedSize(28, 28)
        self._toggle_eye_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)
        self._toggle_eye_btn.clicked.connect(self._toggle_echo_mode)
        input_box_layout.addWidget(self._toggle_eye_btn)

        # Paste Button
        paste_btn = QPushButton("Paste")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.setFixedSize(48, 26)
        paste_btn.setStyleSheet("""
            QPushButton {
                background-color: #24262B;
                color: #D4D4D8;
                border: 1px solid #33363D;
                border-radius: 4px;
                font-size: 8pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #31343B;
                color: #FFFFFF;
            }
        """)
        paste_btn.clicked.connect(self._paste_from_clipboard)
        input_box_layout.addWidget(paste_btn)

        input_container.addWidget(input_box)

        # Inline validation error label (hidden by default)
        self._error_msg_lbl = QLabel("")
        self._error_msg_lbl.setStyleSheet("font-size: 8pt; color: #FF453A; margin-top: 2px;")
        self._error_msg_lbl.setVisible(False)
        input_container.addWidget(self._error_msg_lbl)

        layout.addLayout(input_container)

        # ── 5. Action Buttons (Cancel / Save) ───────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        cancel_btn = QPushButton("Nanti Saja")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(34)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #222428;
                color: #8C8F9A;
                border: 1px solid #2D2F34;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 8.5pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2C2E34;
                color: #FFFFFF;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        action_row.addWidget(cancel_btn)

        action_row.addStretch()

        save_btn = QPushButton("Simpan & Aktifkan")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFixedHeight(34)
        save_fg = "#141517" if _is_light_color(acc1) else "#FFFFFF"
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {acc1};
                color: {save_fg};
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 9pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #FFFFFF;
                color: #141517;
            }}
        """)
        save_btn.clicked.connect(self._on_save_clicked)
        action_row.addWidget(save_btn)

        layout.addLayout(action_row)

    def _load_current_key(self):
        """Pre-populate the key field if available in config."""
        if not self._config:
            return
        key = self._config.get("api_key", "").strip()
        # If it was an error, still show the old key so user can edit or replace it
        if key:
            self._key_input.setText(key)
        self._key_input.setFocus()
        self._key_input.selectAll()

    def _toggle_echo_mode(self):
        """Toggle showing the API key in plain text vs masked."""
        self._show_key = not self._show_key
        if self._show_key:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_eye_btn.setIcon(get_vector_icon("eye_off", color="#FFFFFF", size=14))
        else:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_eye_btn.setIcon(get_vector_icon("eye", color="#8A8D98", size=14))

    def _paste_from_clipboard(self):
        """Paste clipboard content into the input field."""
        text = QApplication.clipboard().text().strip()
        if text:
            self._key_input.setText(text)
            self._error_msg_lbl.setVisible(False)

    def _open_groq_console(self):
        """Open the official Groq API keys page in the user's default browser."""
        QDesktopServices.openUrl(QUrl("https://console.groq.com/keys"))

    def _on_save_clicked(self):
        """Validate, save the new key to config, and close dialog."""
        key = self._key_input.text().strip()
        if not key:
            self._error_msg_lbl.setText("API Key tidak boleh kosong.")
            self._error_msg_lbl.setVisible(True)
            self._key_input.setFocus()
            return

        if not key.startswith("gsk_"):
            self._error_msg_lbl.setText("Peringatan: API Key Groq umumnya diawali dengan 'gsk_'. Pastikan key benar.")
            self._error_msg_lbl.setVisible(True)

        if self._config:
            self._config.set("api_key", key, auto_save=True)

        self.api_key_saved.emit(key)
        self.accept()
