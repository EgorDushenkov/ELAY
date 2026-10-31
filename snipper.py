from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QGuiApplication, QPixmap, QCursor
from PyQt6.QtWidgets import QWidget
from PIL import Image
import io

class SnippingWidget(QWidget):
    """
    Fullscreen translucent sniper overlay for capturing chat screenshots.
    Similar to Lightshot/ShareX UX with crisp borders, dimmed background,
    and dimension tooltip.
    """
    snippet_captured = pyqtSignal(object)  # Emits PIL.Image.Image
    snip_cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self.start_pos: QPoint = None
        self.current_pos: QPoint = None
        self.is_snipping = False
        self.background_pixmap: QPixmap = None

    def start_capture(self):
        """Grabs the entire virtual screen and displays the sniper overlay."""
        # Calculate bounding rectangle of all screens for multi-monitor setups
        screens = QGuiApplication.screens()
        total_rect = QRect()
        for screen in screens:
            total_rect = total_rect.united(screen.geometry())

        self.setGeometry(total_rect)

        # Capture the whole screen desktop
        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen:
            # On Windows, grabbing virtual screen or screen 0
            self.background_pixmap = primary_screen.grabWindow(0, total_rect.x(), total_rect.y(), total_rect.width(), total_rect.height())
        else:
            self.background_pixmap = None

        self.start_pos = None
        self.current_pos = None
        self.is_snipping = False
        self.showFullScreen()
        self.activateWindow()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.snip_cancelled.emit()
            self.close()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.position().toPoint()
            self.current_pos = self.start_pos
            self.is_snipping = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.snip_cancelled.emit()
            self.close()

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.current_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_snipping:
            self.is_snipping = False
            rect = self.get_selected_rect()

            if rect.width() > 40 and rect.height() > 40:
                self.hide()
                # Crop from background pixmap with device pixel ratio support
                if self.background_pixmap:
                    dpr = self.devicePixelRatioF()
                    crop_rect = QRect(
                        int(rect.x() * dpr),
                        int(rect.y() * dpr),
                        int(rect.width() * dpr),
                        int(rect.height() * dpr)
                    )
                    cropped = self.background_pixmap.copy(crop_rect)
                    # Convert to PIL Image
                    image = self._pixmap_to_pil(cropped)
                    self.snippet_captured.emit(image)
                self.close()
            else:
                self.start_pos = None
                self.current_pos = None
                self.update()

    def get_selected_rect(self) -> QRect:
        if not self.start_pos or not self.current_pos:
            return QRect()
        x1 = min(self.start_pos.x(), self.current_pos.x())
        y1 = min(self.start_pos.y(), self.current_pos.y())
        x2 = max(self.start_pos.x(), self.current_pos.x())
        y2 = max(self.start_pos.y(), self.current_pos.y())
        return QRect(x1, y1, x2 - x1, y2 - y1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Draw base screen capture scaled to widget rect
        if self.background_pixmap:
            painter.drawPixmap(self.rect(), self.background_pixmap)

        # 2. Draw darkened overlay over the entire screen
        dim_color = QColor(10, 14, 26, 170)
        selected_rect = self.get_selected_rect()

        if not selected_rect.isValid() or selected_rect.isEmpty():
            painter.fillRect(self.rect(), dim_color)
        else:
            # Fill regions around selection: Top, Bottom, Left, Right
            w = self.width()
            h = self.height()
            rx, ry, rw, rh = selected_rect.x(), selected_rect.y(), selected_rect.width(), selected_rect.height()

            # Top bar
            painter.fillRect(0, 0, w, ry, dim_color)
            # Bottom bar
            painter.fillRect(0, ry + rh, w, h - (ry + rh), dim_color)
            # Left block
            painter.fillRect(0, ry, rx, rh, dim_color)
            # Right block
            painter.fillRect(rx + rw, ry, w - (rx + rw), rh, dim_color)

            # Draw glowing selection border
            border_pen = QPen(QColor(99, 102, 241), 2)  # Indigo accent
            painter.setPen(border_pen)
            painter.drawRect(selected_rect)

            # Draw size badge
            badge_text = f"{rw} × {rh} px"
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            badge_bg = QColor(20, 24, 38, 220)
            text_rect = QRect(rx + 6, ry + rh + 6 if ry + rh + 30 < h else ry - 28, 100, 22)
            painter.setBrush(QBrush(badge_bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(text_rect, 4, 4)
            painter.setPen(QColor(240, 240, 255))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

        # 3. Draw top instruction banner
        banner_w, banner_h = 440, 36
        banner_x = (self.width() - banner_w) // 2
        banner_y = 24
        banner_rect = QRect(banner_x, banner_y, banner_w, banner_h)

        painter.setBrush(QBrush(QColor(15, 23, 42, 230)))
        painter.setPen(QPen(QColor(99, 102, 241, 160), 1))
        painter.drawRoundedRect(banner_rect, 18, 18)

        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        painter.setPen(QColor(241, 245, 249))
        painter.drawText(
            banner_rect,
            Qt.AlignmentFlag.AlignCenter,
            "🎯 Зажмите ЛКМ и выделите область чата | ESC для отмены"
        )

    def _pixmap_to_pil(self, pixmap: QPixmap) -> Image.Image:
        """Converts QPixmap to PIL Image using QBuffer."""
        q_buffer = QBuffer()
        q_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(q_buffer, "PNG")
        raw_bytes = bytes(q_buffer.data())
        q_buffer.close()
        return Image.open(io.BytesIO(raw_bytes))

