from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtCore import QUrl
from config import load_config, save_config
from gemini_service import GeminiChatAnalyzer


class TestConnectionThread(QThread):
    result_signal = pyqtSignal(bool, str)

    def __init__(self, api_key: str, model_name: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name

    def run(self):
        analyzer = GeminiChatAnalyzer(self.api_key, self.model_name)
        success, message = analyzer.test_connection()
        self.result_signal.emit(success, message)


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки VibeSense AI")
        self.setFixedSize(520, 440)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #6366f1;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #4f46e5;
                border: 1px solid #334155;
            }
            QPushButton {
                background-color: #334155;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton#primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
            }
            QPushButton#primaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
            }
            QPushButton#linkBtn {
                background: transparent;
                color: #38bdf8;
                text-decoration: underline;
                padding: 0;
                font-weight: 500;
            }
            QPushButton#linkBtn:hover {
                color: #7dd3fc;
            }
        """)

        self.test_thread = None
        self._init_ui()
        self._load_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title_label = QLabel("⚙️ Настройки подключения")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 4px;")
        layout.addWidget(title_label)

        # API Key Section
        api_header_layout = QHBoxLayout()
        key_label = QLabel("Google Gemini API Key:")
        key_label.setStyleSheet("font-weight: 600;")
        api_header_layout.addWidget(key_label)
        api_header_layout.addStretch()

        get_key_btn = QPushButton("Получить ключ бесплатно ↗")
        get_key_btn.setObjectName("linkBtn")
        get_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        get_key_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/apikey")))
        api_header_layout.addWidget(get_key_btn)
        layout.addLayout(api_header_layout)

        # API Key Input + visibility toggle
        key_input_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Вставьте ключ вида AIzaSy...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input_layout.addWidget(self.api_key_input)

        self.toggle_key_visibility_btn = QPushButton("👁️")
        self.toggle_key_visibility_btn.setFixedWidth(42)
        self.toggle_key_visibility_btn.setToolTip("Показать / скрыть ключ")
        self.toggle_key_visibility_btn.clicked.connect(self._toggle_key_visibility)
        key_input_layout.addWidget(self.toggle_key_visibility_btn)
        layout.addLayout(key_input_layout)

        # Test key button & status label
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("Проверить ключ")
        self.test_btn.clicked.connect(self._test_api_key)
        test_layout.addWidget(self.test_btn)

        self.test_status_label = QLabel("")
        self.test_status_label.setStyleSheet("font-size: 12px;")
        test_layout.addWidget(self.test_status_label)
        test_layout.addStretch()
        layout.addLayout(test_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #1e293b; background-color: #1e293b; max-height: 1px;")
        layout.addWidget(divider)

        # Model selection
        model_label = QLabel("Модель Gemini:")
        model_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ])
        layout.addWidget(self.model_combo)

        # Hotkey selection
        hotkey_label = QLabel("Горячая клавиша для скриншота:")
        hotkey_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(hotkey_label)

        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems([
            "alt+s",
            "ctrl+shift+s",
            "alt+x",
            "ctrl+space",
        ])
        layout.addWidget(self.hotkey_combo)

        layout.addStretch()

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _toggle_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _load_values(self):
        config = load_config()
        self.api_key_input.setText(config.get("gemini_api_key", ""))
        model = config.get("model_name", "gemini-2.5-flash")
        idx = self.model_combo.findText(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

        hotkey = config.get("hotkey", "alt+s")
        h_idx = self.hotkey_combo.findText(hotkey)
        if h_idx >= 0:
            self.hotkey_combo.setCurrentIndex(h_idx)

    def _test_api_key(self):
        key = self.api_key_input.text().strip()
        if not key:
            self.test_status_label.setStyleSheet("color: #ef4444;")
            self.test_status_label.setText("⚠️ Введите ключ перед проверкой")
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText("Проверка...")
        self.test_status_label.setStyleSheet("color: #38bdf8;")
        self.test_status_label.setText("Отправка тестового запроса...")

        model = self.model_combo.currentText()
        self.test_thread = TestConnectionThread(key, model)
        self.test_thread.result_signal.connect(self._on_test_finished)
        self.test_thread.start()

    def _on_test_finished(self, success: bool, message: str):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Проверить ключ")
        if success:
            self.test_status_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.test_status_label.setText("✓ Ключ активен и работает!")
        else:
            self.test_status_label.setStyleSheet("color: #ef4444;")
            self.test_status_label.setText(f"✕ {message}")

    def _save_settings(self):
        config = load_config()
        config["gemini_api_key"] = self.api_key_input.text().strip()
        config["model_name"] = self.model_combo.currentText()
        config["hotkey"] = self.hotkey_combo.currentText()
        save_config(config)
        self.settings_saved.emit()
        self.accept()

