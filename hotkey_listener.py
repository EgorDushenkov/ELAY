from PyQt6.QtCore import QObject, pyqtSignal
import threading

class GlobalHotkeyListener(QObject):
    """
    Listens for a global hotkey across the OS.
    Uses keyboard module with automatic fallback to pynput
    for maximum compatibility without needing administrator privileges.
    """
    hotkey_triggered = pyqtSignal()

    def __init__(self, hotkey: str = "alt+s"):
        super().__init__()
        self.hotkey = hotkey.lower().strip()
        self._hooked = False
        self._engine = None  # "keyboard" or "pynput"
        self._pynput_listener = None
        self._lock = threading.RLock()

    def start(self):
        self.register_hotkey(self.hotkey)

    def register_hotkey(self, hotkey_str: str):
        with self._lock:
            self.stop()
            self.hotkey = hotkey_str.lower().strip()

            # Attempt 1: keyboard library
            try:
                import keyboard
                keyboard.add_hotkey(self.hotkey, self._on_triggered)
                self._hooked = True
                self._engine = "keyboard"
                print(f"[Hotkey] Registered '{self.hotkey}' via keyboard hook.")
                return
            except Exception as e:
                print(f"[Hotkey] Notice: keyboard module hook unavailable ({e}), trying pynput fallback...")

            # Attempt 2: pynput fallback
            try:
                from pynput import keyboard as pk

                # Convert format: "alt+s" -> "<alt>+s", "ctrl+shift+s" -> "<ctrl>+<shift>+s"
                parts = self.hotkey.split("+")
                pynput_parts = []
                for p in parts:
                    p = p.strip()
                    if p in ("alt", "ctrl", "shift", "cmd", "windows"):
                        pynput_parts.append(f"<{p}>")
                    elif p == "space":
                        pynput_parts.append("<space>")
                    else:
                        pynput_parts.append(p)
                pynput_key_combo = "+".join(pynput_parts)

                self._pynput_listener = pk.GlobalHotKeys({
                    pynput_key_combo: self._on_triggered
                })
                self._pynput_listener.daemon = True
                self._pynput_listener.start()
                self._hooked = True
                self._engine = "pynput"
                print(f"[Hotkey] Registered '{pynput_key_combo}' via pynput hook.")
            except Exception as ex:
                print(f"[Hotkey] Failed to register hotkey with both engines: {ex}")
                self._hooked = False

    def stop(self):
        with self._lock:
            if self._hooked:
                if self._engine == "keyboard":
                    try:
                        import keyboard
                        keyboard.remove_hotkey(self.hotkey)
                    except Exception:
                        pass
                elif self._engine == "pynput" and self._pynput_listener:
                    try:
                        self._pynput_listener.stop()
                    except Exception:
                        pass
                    self._pynput_listener = None
                self._hooked = False
                self._engine = None

    def _on_triggered(self):
        self.hotkey_triggered.emit()
