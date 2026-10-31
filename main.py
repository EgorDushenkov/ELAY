import sys
import os
import warnings

# Safe stdout/stderr for pyinstaller --noconsole mode
class SafeStream:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass

if sys.stdout is None:
    sys.stdout = SafeStream()
if sys.stderr is None:
    sys.stderr = SafeStream()

# Ensure UTF-8 console output on Windows if console is present
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Suppress harmless deprecation warnings in console
warnings.filterwarnings("ignore")
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

from config import load_config
from snipper import SnippingWidget
from chat_overlay import FloatingOverlayWindow
from hotkey_listener import GlobalHotkeyListener


def create_app_icon() -> QIcon:
    """Generates a modern circular gradient app icon dynamically."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Circle background with gradient
    painter.setBrush(QColor(99, 102, 241))  # Indigo
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 60, 60, 16, 16)

    # Inner subtle circle
    painter.setBrush(QColor(129, 140, 248))
    painter.drawEllipse(12, 12, 40, 40)

    # Target / Sparkle glyph
    painter.setFont(QFont("Segoe UI Emoji", 24))
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🎯")

    painter.end()
    return QIcon(pixmap)


class VibeSenseApp:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.config = load_config()

        # Generate app icon
        self.app_icon = create_app_icon()
        self.qapp.setWindowIcon(self.app_icon)

        # 1. Create windows and widgets
        self.snipper = SnippingWidget()
        self.overlay = FloatingOverlayWindow()
        self.settings_dialog = None

        # 2. Connect signals
        # When sniper captures an area -> add to overlay gallery
        self.snipper.snippet_captured.connect(self.overlay.add_captured_image)
        # When snipping is cancelled (Esc / Right Click) -> restore overlay
        self.snipper.snip_cancelled.connect(self.overlay.show)
        # When user clicks "Добавить снимок" inside overlay -> launch snipper
        self.overlay.request_snip.connect(self.start_snip)

        # 3. Setup global hotkey (Alt+S toggles the overlay window!)
        hotkey = self.config.get("hotkey", "alt+s")
        self.hotkey_listener = GlobalHotkeyListener(hotkey)
        self.hotkey_listener.hotkey_triggered.connect(self.toggle_overlay)
        self.hotkey_listener.start()

        # 4. Setup System Tray
        self._setup_tray()

        # Show overlay window on first start so the user immediately sees it
        self.overlay.show()
        self.overlay.activateWindow()

        print("===================================================")
        print(" [OK] VibeSense AI успешно запущен!")
        print(f" [OK] Горячая клавиша: {hotkey.upper()} (показать / скрыть окно)")
        print(" [OK] Снимок чата делается по кнопке в самом окне.")
        print(" [OK] Плавающее окно открыто в правом верхнем углу.")
        print(" [OK] Также доступно в системном трее Windows.")
        print("===================================================")

    def toggle_overlay(self):
        """Toggles overlay visibility on global hotkey."""
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()
            self.overlay.raise_()
            self.overlay.activateWindow()

    def start_snip(self):
        """Hides the overlay temporarily and opens the sniper."""
        print("[VibeSense] Режим захвата экрана...")
        self.overlay.hide()
        self.snipper.start_capture()

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("[Tray] System tray is not available on this system.")
            return

        self.tray_icon = QSystemTrayIcon(self.app_icon, self.qapp)
        self.tray_icon.setToolTip("VibeSense AI — Анализатор вайба переписок (Alt+S)")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #4f46e5;
                color: #ffffff;
            }
        """)

        snip_action = tray_menu.addAction("📸 Сделать снимок чата")
        snip_action.triggered.connect(self.start_snip)

        show_action = tray_menu.addAction("🪟 Показать / скрыть оверлей (Alt+S)")
        show_action.triggered.connect(self.toggle_overlay)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("✕ Выход")
        quit_action.triggered.connect(self._quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick or reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_overlay()

    def _show_overlay(self):
        self.overlay.show()
        self.overlay.activateWindow()

    def _quit_app(self):
        self.hotkey_listener.stop()
        self.qapp.quit()


def main():
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray!

    app_instance = VibeSenseApp(app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

