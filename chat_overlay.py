import io
from typing import Optional, List
from PIL import Image

from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QThread, QTimer, QSize
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont,
    QIcon, QClipboard, QGuiApplication, QCursor
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QScrollArea, QFrame, QProgressBar, QComboBox,
    QSizePolicy, QMessageBox, QApplication
)

from config import load_config, save_config, GOAL_PRESETS, EMBEDDED_API_KEY
from gemini_service import GeminiChatAnalyzer, ChatAnalysisResult


class DraftTextEdit(QTextEdit):
    submit_requested = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.submit_requested.emit()
            return
        super().keyPressEvent(event)


class AnalysisThread(QThread):
    finished_signal = pyqtSignal(object)  # ChatAnalysisResult
    error_signal = pyqtSignal(str)

    def __init__(self, analyzer: GeminiChatAnalyzer, images: list, goal_title: str, goal_instruction: str, draft: str):
        super().__init__()
        self.analyzer = analyzer
        self.images = images
        self.goal_title = goal_title
        self.goal_instruction = goal_instruction
        self.draft = draft

    def run(self):
        try:
            result = self.analyzer.analyze_chat(
                images=self.images,
                goal_title=self.goal_title,
                goal_instruction=self.goal_instruction,
                draft_reply=self.draft
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class FitScrollArea(QScrollArea):
    """QScrollArea that strictly constrains the inner widget width to the viewport width."""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.widget():
            self.widget().setFixedWidth(self.viewport().width())


class FloatingOverlayWindow(QWidget):
    request_snip = pyqtSignal()
    MAX_IMAGES = 10

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.captured_images: List[Image.Image] = []
        self.selected_preset_idx = 0
        self.drag_position = QPoint()
        self.analysis_thread: Optional[AnalysisThread] = None

        self._setup_window_flags()
        self._setup_styles()
        self._build_ui()
        self.update_preset_buttons()
        self._refresh_gallery()

    def _setup_window_flags(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(550, 760)
        self.setMinimumWidth(500)

        # Restore position if saved
        saved_pos = self.config.get("window_pos")
        if saved_pos and len(saved_pos) == 2:
            self.move(saved_pos[0], saved_pos[1])
        else:
            # Default to top right corner of primary screen
            screen = QGuiApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                self.move(geom.right() - 580, geom.top() + 50)

    def _setup_styles(self):
        self.setStyleSheet("""
            QWidget#MainContainer {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 16px;
            }
            QLabel {
                color: #e2e8f0;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f172a;
                width: 6px;
                border-radius: 3px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6366f1;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QTextEdit {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 10px;
                padding: 10px;
                color: #f9fafb;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 1px solid #6366f1;
            }
            QPushButton {
                font-family: 'Segoe UI', sans-serif;
                border-radius: 8px;
            }
        """)

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)

        # Main styled card container
        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 16)
        container_layout.setSpacing(12)

        # 1. Header (Title bar with Drag and Action buttons)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_label = QLabel("🎯")
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        header_layout.addWidget(icon_label)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(0)
        app_title = QLabel("VibeSense AI")
        app_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        app_title.setStyleSheet("color: #ffffff;")
        title_vbox.addWidget(app_title)
        header_layout.addLayout(title_vbox)

        header_layout.addStretch()

        # Model Selector ComboBox right in the title bar
        self.model_combo = QComboBox()
        self.model_combo.addItem("⚡ 2.5 Flash", "gemini-2.5-flash")
        self.model_combo.addItem("🚀 3.5 Flash Lite", "gemini-3.5-flash-lite")
        self.model_combo.setToolTip("Выбор модели. Если лимит 2.5 Flash исчерпан, автоматически переключится на 3.5 Flash Lite")
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px 8px;
                color: #e2e8f0;
                font-size: 11px;
                font-weight: 600;
            }
            QComboBox:hover {
                border: 1px solid #6366f1;
            }
            QComboBox::drop-down {
                border: none;
                width: 14px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #ffffff;
                selection-background-color: #4f46e5;
                border: 1px solid #334155;
            }
        """)

        # Set saved model from config
        saved_model = self.config.get("model_name", "gemini-2.5-flash")
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == saved_model:
                self.model_combo.setCurrentIndex(i)
                break
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        header_layout.addWidget(self.model_combo)

        # Minimize/Hide button
        self.hide_btn = QPushButton("✕")
        self.hide_btn.setFixedSize(30, 30)
        self.hide_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: none;
                border-radius: 6px;
                color: #94a3b8;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        self.hide_btn.setToolTip("Свернуть оверлей (Alt+S откроет снова)")
        self.hide_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.hide_btn)

        container_layout.addLayout(header_layout)

        # Scroll area for body
        self.scroll_area = FitScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.body_layout = QVBoxLayout(scroll_content)
        self.body_layout.setContentsMargins(0, 0, 4, 0)
        self.body_layout.setSpacing(12)

        # 2. Screenshot Multi-Gallery Section (up to 10 screenshots)
        self._build_gallery_section()

        # 3. Goal / Tone Selector Pills (2-column grid without horizontal overflow)
        self._build_presets_section()

        # 4. Draft Input Section
        self._build_draft_section()

        # 5. Analyze Button & Progress
        self._build_action_section()

        # 6. Results Container
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)
        self.body_layout.addWidget(self.results_container)

        self.scroll_area.setWidget(scroll_content)
        container_layout.addWidget(self.scroll_area)

        # Bottom Shortcut hint
        bottom_hint = QLabel("💡 Alt+S: скрыть / открыть оверлей | Снимок: по кнопке в окне")
        bottom_hint.setStyleSheet("color: #64748b; font-size: 11px; text-align: center;")
        bottom_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(bottom_hint)

        root_layout.addWidget(self.container)

    def _build_gallery_section(self):
        """Builds the multi-image screenshot gallery container."""
        self.gallery_card = QFrame()
        self.gallery_card.setObjectName("GalleryCard")
        self.gallery_card.setStyleSheet("""
            QFrame#GalleryCard {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 6px;
            }
        """)
        self.gallery_vbox = QVBoxLayout(self.gallery_card)
        self.gallery_vbox.setContentsMargins(10, 10, 10, 10)
        self.gallery_vbox.setSpacing(8)

        # Header: Title + Action buttons
        hdr_layout = QHBoxLayout()
        self.gallery_title = QLabel("📸 Скриншоты переписки (0/10)")
        self.gallery_title.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        hdr_layout.addWidget(self.gallery_title)
        hdr_layout.addStretch()

        self.clear_all_btn = QPushButton("🗑️ Очистить")
        self.clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #f87171;
                font-size: 11px;
                font-weight: 500;
                padding: 4px 8px;
                border: 1px solid #7f1d1d;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #450a0a;
                color: #fca5a5;
            }
        """)
        self.clear_all_btn.clicked.connect(self.clear_all_images)
        self.clear_all_btn.hide()
        hdr_layout.addWidget(self.clear_all_btn)

        self.add_snip_btn = QPushButton("📸 Сделать снимок")
        self.add_snip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_snip_btn.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 5px 12px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6366f1;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #94a3b8;
            }
        """)
        self.add_snip_btn.clicked.connect(self._trigger_snipper)
        hdr_layout.addWidget(self.add_snip_btn)
        self.gallery_vbox.addLayout(hdr_layout)

        # Gallery content area (thumbnails container)
        self.gallery_content = QWidget()
        self.gallery_content_layout = QVBoxLayout(self.gallery_content)
        self.gallery_content_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_content_layout.setSpacing(6)
        self.gallery_vbox.addWidget(self.gallery_content)

        self.body_layout.addWidget(self.gallery_card)

    def _refresh_gallery(self):
        """Re-renders thumbnail cards or empty state depending on captured images."""
        count = len(self.captured_images)
        self.gallery_title.setText(f"📸 Скриншоты переписки ({count}/{self.MAX_IMAGES})")

        # Clear existing items in gallery content
        while self.gallery_content_layout.count():
            item = self.gallery_content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if count == 0:
            self.clear_all_btn.hide()
            self.add_snip_btn.setText("📸 Сделать снимок")
            self.add_snip_btn.setEnabled(True)

            # Empty state
            empty_box = QFrame()
            empty_box.setStyleSheet("""
                QFrame {
                    background-color: #0b0f19;
                    border: 1px dashed #334155;
                    border-radius: 8px;
                    padding: 14px;
                }
            """)
            e_layout = QVBoxLayout(empty_box)
            e_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_layout.setSpacing(6)

            e_icon = QLabel("📷")
            e_icon.setFont(QFont("Segoe UI Emoji", 20))
            e_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_layout.addWidget(e_icon)

            e_text = QLabel("Добавьте до 10 скриншотов диалога")
            e_text.setStyleSheet("color: #e2e8f0; font-size: 12px; font-weight: 600;")
            e_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_layout.addWidget(e_text)

            e_sub = QLabel("Нажмите кнопку выше, чтобы выделить область чата на экране")
            e_sub.setStyleSheet("color: #64748b; font-size: 11px;")
            e_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e_layout.addWidget(e_sub)

            self.gallery_content_layout.addWidget(empty_box)
        else:
            self.clear_all_btn.show()
            if count < self.MAX_IMAGES:
                self.add_snip_btn.setEnabled(True)
                self.add_snip_btn.setText(f"+ Добавить ({count}/{self.MAX_IMAGES})")
            else:
                self.add_snip_btn.setEnabled(False)
                self.add_snip_btn.setText("Лимит (10/10)")

            # Thumbnails scroll container
            thumb_scroll = QScrollArea()
            thumb_scroll.setFixedHeight(105)
            thumb_scroll.setWidgetResizable(True)
            thumb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            thumb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            thumb_scroll.setStyleSheet("""
                QScrollArea { background: transparent; border: none; }
                QScrollBar:horizontal {
                    height: 5px;
                    background: #0f172a;
                    border-radius: 2px;
                }
                QScrollBar::handle:horizontal {
                    background: #334155;
                    border-radius: 2px;
                }
            """)

            thumb_widget = QWidget()
            thumb_layout = QHBoxLayout(thumb_widget)
            thumb_layout.setContentsMargins(0, 0, 0, 0)
            thumb_layout.setSpacing(8)

            for idx, img in enumerate(self.captured_images):
                card = self._create_thumbnail_card(idx, img)
                thumb_layout.addWidget(card)

            # If under limit, add a quick "+" card
            if count < self.MAX_IMAGES:
                add_card = self._create_add_tile_card()
                thumb_layout.addWidget(add_card)

            thumb_layout.addStretch()
            thumb_scroll.setWidget(thumb_widget)
            self.gallery_content_layout.addWidget(thumb_scroll)

            # Order explanation hint
            hint_lbl = QLabel(f"💬 Захвачено {count} фрагм. диалога (будут переданы модели по порядку хронологии).")
            hint_lbl.setStyleSheet("color: #818cf8; font-size: 11px; margin-top: 2px;")
            self.gallery_content_layout.addWidget(hint_lbl)

    def _create_thumbnail_card(self, index: int, image: Image.Image) -> QFrame:
        card = QFrame()
        card.setFixedSize(100, 92)
        card.setStyleSheet("""
            QFrame {
                background-color: #172033;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 1px solid #6366f1;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(2)

        # Header: Index Badge + Delete (✕) Button
        hdr = QHBoxLayout()
        hdr.setContentsMargins(2, 0, 2, 0)
        badge = QLabel(f"#{index + 1}")
        badge.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 10px;")
        hdr.addWidget(badge)
        hdr.addStretch()

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(16, 16)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 10px;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)
        del_btn.setToolTip("Удалить этот снимок")
        del_btn.clicked.connect(lambda checked, idx=index: self.remove_captured_image(idx))
        hdr.addWidget(del_btn)
        c_layout.addLayout(hdr)

        # Thumbnail Image
        thumb_lbl = QLabel()
        thumb_lbl.setFixedSize(92, 48)
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_lbl.setStyleSheet("background-color: #0b0f19; border-radius: 4px;")

        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        buffer.seek(0)
        qimg = QImage()
        qimg.loadFromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimg)

        scaled = pixmap.scaled(
            92, 48,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        thumb_lbl.setPixmap(scaled)
        c_layout.addWidget(thumb_lbl)

        # Size footer
        size_lbl = QLabel(f"{image.width}×{image.height}")
        size_lbl.setStyleSheet("color: #64748b; font-size: 9px; text-align: center;")
        size_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(size_lbl)

        return card

    def _create_add_tile_card(self) -> QPushButton:
        btn = QPushButton("+\nСнимок")
        btn.setFixedSize(65, 92)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0f172a;
                color: #818cf8;
                border: 1px dashed #4338ca;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1e1b4b;
                border: 1px dashed #6366f1;
                color: #a5b4fc;
            }
        """)
        btn.clicked.connect(self._trigger_snipper)
        return btn

    def add_captured_image(self, image: Image.Image):
        """Adds a newly captured screenshot to the gallery."""
        if len(self.captured_images) < self.MAX_IMAGES:
            self.captured_images.append(image)
            self._refresh_gallery()
        else:
            QMessageBox.warning(
                self,
                "Лимит скриншотов",
                f"Достигнут максимум скриншотов ({self.MAX_IMAGES}). Удалите ненужные, чтобы добавить новые."
            )
        self.show()
        self.activateWindow()

    def set_captured_image(self, image: Image.Image):
        """Compatibility wrapper."""
        self.add_captured_image(image)

    def remove_captured_image(self, index: int):
        if 0 <= index < len(self.captured_images):
            self.captured_images.pop(index)
            self._refresh_gallery()

    def clear_all_images(self):
        self.captured_images.clear()
        self._refresh_gallery()

    def _build_presets_section(self):
        """Builds goal selector in a clean 2-column grid with custom goal input."""
        presets_label = QLabel("🎯 Цель твоего ответа:")
        presets_label.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        self.body_layout.addWidget(presets_label)

        self.pills_container = QWidget()
        pills_layout = QGridLayout(self.pills_container)
        pills_layout.setContentsMargins(0, 0, 0, 0)
        pills_layout.setSpacing(6)

        self.preset_buttons = []
        for i, preset in enumerate(GOAL_PRESETS):
            btn = QPushButton(preset["label"])
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, idx=i: self._select_preset(idx))
            self.preset_buttons.append(btn)
            row = i // 2
            col = i % 2
            pills_layout.addWidget(btn, row, col)

        self.body_layout.addWidget(self.pills_container)

        # Custom Goal Input Box
        self.custom_goal_frame = QFrame()
        self.custom_goal_frame.setObjectName("CustomGoalFrame")
        self.custom_goal_frame.setStyleSheet("""
            QFrame#CustomGoalFrame {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 2px 8px;
            }
            QFrame#CustomGoalFrame:hover {
                border: 1px solid #334155;
            }
        """)
        cg_layout = QHBoxLayout(self.custom_goal_frame)
        cg_layout.setContentsMargins(6, 4, 6, 4)
        cg_layout.setSpacing(8)

        cg_icon = QLabel("✏️")
        cg_icon.setFont(QFont("Segoe UI Emoji", 11))
        cg_layout.addWidget(cg_icon)

        self.custom_goal_edit = QLineEdit()
        self.custom_goal_edit.setPlaceholderText("Или своя цель: например, вернуть долг, вывести на скам...")
        self.custom_goal_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f1f5f9;
                font-size: 12px;
                padding: 4px 0px;
            }
            QLineEdit:focus {
                border: none;
            }
        """)
        self.custom_goal_edit.textChanged.connect(self._on_custom_goal_changed)
        self.custom_goal_edit.returnPressed.connect(self._start_analysis)
        cg_layout.addWidget(self.custom_goal_edit)

        self.clear_custom_goal_btn = QPushButton("✕")
        self.clear_custom_goal_btn.setFixedSize(18, 18)
        self.clear_custom_goal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_custom_goal_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: none;
                border-radius: 9px;
                font-size: 10px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background: #334155;
                color: #ffffff;
            }
        """)
        self.clear_custom_goal_btn.setToolTip("Очистить свою цель")
        self.clear_custom_goal_btn.clicked.connect(self._clear_custom_goal)
        self.clear_custom_goal_btn.hide()
        cg_layout.addWidget(self.clear_custom_goal_btn)

        self.body_layout.addWidget(self.custom_goal_frame)

    def _build_draft_section(self):
        draft_label = QLabel("✍️ Твой черновик ответа (необязательно):")
        draft_label.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        self.body_layout.addWidget(draft_label)

        self.draft_edit = DraftTextEdit()
        self.draft_edit.setPlaceholderText("Напиши как бы ответил ты (или оставь пустым, чтобы получить идеи с нуля)... [Ctrl+Enter для анализа]")
        self.draft_edit.setFixedHeight(68)
        self.draft_edit.submit_requested.connect(self._start_analysis)
        self.body_layout.addWidget(self.draft_edit)

    def _build_action_section(self):
        self.analyze_btn = QPushButton("🚀 Анализировать вайб переписки")
        self.analyze_btn.setFixedHeight(44)
        self.analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:0.5 #6366f1, stop:1 #38bdf8);
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:0.5 #4f46e5, stop:1 #0284c7);
            }
            QPushButton:disabled {
                background: #334155;
                color: #94a3b8;
            }
        """)
        self.analyze_btn.clicked.connect(self._start_analysis)
        self.body_layout.addWidget(self.analyze_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Infinite spinner
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1e293b;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background: #6366f1;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        self.body_layout.addWidget(self.progress_bar)

    def _on_custom_goal_changed(self, text: str):
        has_text = bool(text.strip())
        self.clear_custom_goal_btn.setVisible(has_text)
        if has_text:
            self.custom_goal_frame.setStyleSheet("""
                QFrame#CustomGoalFrame {
                    background-color: #131b2e;
                    border: 1px solid #6366f1;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
            """)
        else:
            self.custom_goal_frame.setStyleSheet("""
                QFrame#CustomGoalFrame {
                    background-color: #111827;
                    border: 1px solid #1f2937;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
                QFrame#CustomGoalFrame:hover {
                    border: 1px solid #334155;
                }
            """)
        self.update_preset_buttons()

    def _clear_custom_goal(self):
        self.custom_goal_edit.clear()
        if self.selected_preset_idx < 0:
            self.selected_preset_idx = 0
        self.update_preset_buttons()

    def _select_preset(self, index: int):
        self.selected_preset_idx = index
        if self.custom_goal_edit.text():
            self.custom_goal_edit.blockSignals(True)
            self.custom_goal_edit.clear()
            self.clear_custom_goal_btn.hide()
            self.custom_goal_frame.setStyleSheet("""
                QFrame#CustomGoalFrame {
                    background-color: #111827;
                    border: 1px solid #1f2937;
                    border-radius: 8px;
                    padding: 2px 8px;
                }
                QFrame#CustomGoalFrame:hover {
                    border: 1px solid #334155;
                }
            """)
            self.custom_goal_edit.blockSignals(False)
        self.update_preset_buttons()

    def update_preset_buttons(self):
        active_style = """
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                border: 1px solid #818cf8;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 600;
                text-align: left;
            }
        """
        inactive_style = """
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 11px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #283548;
                color: #e2e8f0;
                border: 1px solid #475569;
            }
        """
        custom_active = bool(self.custom_goal_edit.text().strip())
        for i, btn in enumerate(self.preset_buttons):
            if not custom_active and i == self.selected_preset_idx:
                btn.setStyleSheet(active_style)
                btn.setChecked(True)
            else:
                btn.setStyleSheet(inactive_style)
                btn.setChecked(False)

    def _on_model_changed(self, index: int):
        model_id = self.model_combo.itemData(index)
        if model_id:
            self.config["model_name"] = model_id
            save_config(self.config)

    def _trigger_snipper(self):
        self.request_snip.emit()

    def _start_analysis(self):
        key = self.config.get("gemini_api_key", EMBEDDED_API_KEY).strip() or EMBEDDED_API_KEY
        if not key:
            QMessageBox.warning(
                self,
                "Ключ не найден",
                "API ключ Gemini не настроен."
            )
            return

        if not self.captured_images:
            QMessageBox.information(
                self,
                "Сделайте скриншот",
                "Добавьте хотя бы один скриншот переписки с помощью кнопки '📸 Сделать снимок'."
            )
            self._trigger_snipper()
            return

        custom_goal = self.custom_goal_edit.text().strip()
        if custom_goal:
            goal_title = f"Своя цель: {custom_goal}"
            goal_instruction = (
                f"Пользователь сформулировал индивидуальную цель: '{custom_goal}'. "
                "Адаптируй и настрой все ответы и советы именно под достижение этой цели "
                "в рамках негласных правил и вайба этого чата."
            )
        else:
            if self.selected_preset_idx < 0:
                self.selected_preset_idx = 0
            preset = GOAL_PRESETS[self.selected_preset_idx]
            goal_title = preset["label"]
            goal_instruction = preset["instruction"]

        draft_text = self.draft_edit.toPlainText().strip()
        model_name = self.model_combo.currentData() or self.config.get("model_name", "gemini-2.5-flash")

        analyzer = GeminiChatAnalyzer(api_key=key, model_name=model_name)

        # UI state: loading
        count = len(self.captured_images)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText(f"🤖 Читаем между строк ({count} скринш.)...")
        self.progress_bar.show()

        # Run in background thread to keep UI completely responsive
        self.analysis_thread = AnalysisThread(
            analyzer=analyzer,
            images=list(self.captured_images),
            goal_title=goal_title,
            goal_instruction=goal_instruction,
            draft=draft_text
        )
        self.analysis_thread.finished_signal.connect(self._on_analysis_success)
        self.analysis_thread.error_signal.connect(self._on_analysis_error)
        self.analysis_thread.start()

    def _on_analysis_success(self, result: ChatAnalysisResult):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🚀 Анализировать снова")
        self.progress_bar.hide()

        # If fallback triggered or result mentions 3.5 Flash Lite, update combo box
        if "3.5 Flash Lite" in result.summary or "3.5-flash-lite" in result.summary:
            self.model_combo.blockSignals(True)
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == "gemini-3.5-flash-lite":
                    self.model_combo.setCurrentIndex(i)
                    break
            self.config["model_name"] = "gemini-3.5-flash-lite"
            save_config(self.config)
            self.model_combo.blockSignals(False)

        self._render_results(result)

    def _on_analysis_error(self, error_msg: str):
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🚀 Анализировать вайб переписки")
        self.progress_bar.hide()

        err_box = QMessageBox(self)
        err_box.setIcon(QMessageBox.Icon.Critical)
        err_box.setWindowTitle("Ошибка анализа")
        err_box.setText("Не удалось проанализировать переписку.")
        err_box.setInformativeText(error_msg)
        err_box.setStyleSheet("background-color: #0f172a; color: #ffffff;")
        err_box.exec()

    def _render_results(self, result: ChatAnalysisResult):
        # Clear previous results
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 1. ATMOSPHERE CARD
        atm = result.atmosphere
        atm_card = QFrame()
        atm_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        atm_card.setMinimumWidth(0)
        atm_card.setStyleSheet("""
            QFrame {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        atm_layout = QVBoxLayout(atm_card)
        atm_layout.setSpacing(10)

        # Summary header
        sum_label = QLabel(f"💬 {result.summary}")
        sum_label.setWordWrap(True)
        sum_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sum_label.setMinimumWidth(0)
        sum_label.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 600; line-height: 1.3;")
        atm_layout.addWidget(sum_label)

        # Vibe Tag (with word wrap and zero min width)
        vibe_badge = QLabel(f"🎭 Вайб: {atm.vibe}")
        vibe_badge.setWordWrap(True)
        vibe_badge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        vibe_badge.setMinimumWidth(0)
        vibe_badge.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")
        atm_layout.addWidget(vibe_badge)

        # Tension & Formality gauges
        gauges_layout = QVBoxLayout()
        gauges_layout.setSpacing(6)

        # Tension (Накал)
        tension_row = QHBoxLayout()
        tension_title = QLabel("🔥 Напряжение / Накал:")
        tension_title.setStyleSheet("color: #94a3b8; font-size: 11px;")
        tension_val = QLabel(f"{atm.tension_score}/10")
        t_color = "#10b981" if atm.tension_score <= 3 else ("#f59e0b" if atm.tension_score <= 6 else "#ef4444")
        tension_val.setStyleSheet(f"color: {t_color}; font-weight: bold; font-size: 12px;")
        tension_row.addWidget(tension_title)
        tension_row.addStretch()
        tension_row.addWidget(tension_val)
        gauges_layout.addLayout(tension_row)

        t_bar = QProgressBar()
        t_bar.setRange(0, 10)
        t_bar.setValue(atm.tension_score)
        t_bar.setFixedHeight(6)
        t_bar.setTextVisible(False)
        t_bar.setStyleSheet(f"""
            QProgressBar {{ background: #1e293b; border-radius: 3px; border: none; }}
            QProgressBar::chunk {{ background: {t_color}; border-radius: 3px; }}
        """)
        gauges_layout.addWidget(t_bar)

        # Formality (Формальность)
        form_row = QHBoxLayout()
        form_title = QLabel("👔 Формальность:")
        form_title.setStyleSheet("color: #94a3b8; font-size: 11px;")
        form_val = QLabel(f"{atm.formality_score}/10")
        form_val.setStyleSheet("color: #818cf8; font-weight: bold; font-size: 12px;")
        form_row.addWidget(form_title)
        form_row.addStretch()
        form_row.addWidget(form_val)
        gauges_layout.addLayout(form_row)

        f_bar = QProgressBar()
        f_bar.setRange(0, 10)
        f_bar.setValue(atm.formality_score)
        f_bar.setFixedHeight(6)
        f_bar.setTextVisible(False)
        f_bar.setStyleSheet("""
            QProgressBar { background: #1e293b; border-radius: 3px; border: none; }
            QProgressBar::chunk { background: #818cf8; border-radius: 3px; }
        """)
        gauges_layout.addWidget(f_bar)
        atm_layout.addLayout(gauges_layout)

        # Social distance & Rhythm
        meta_label = QLabel(f"👥 Дистанция: {atm.social_distance} • Темп: {atm.pace_and_rhythm}")
        meta_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        meta_label.setWordWrap(True)
        meta_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        meta_label.setMinimumWidth(0)
        atm_layout.addWidget(meta_label)

        # Unspoken rules banner
        rules_box = QFrame()
        rules_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        rules_box.setMinimumWidth(0)
        rules_box.setStyleSheet("background-color: #1e1b4b; border-radius: 8px; border: 1px solid #4338ca;")
        r_box_layout = QVBoxLayout(rules_box)
        r_box_layout.setContentsMargins(10, 8, 10, 8)
        rules_title = QLabel("⚡ Негласные правила этого чата:")
        rules_title.setStyleSheet("color: #a5b4fc; font-weight: bold; font-size: 11px;")
        r_box_layout.addWidget(rules_title)
        rules_text = QLabel(atm.unspoken_rules)
        rules_text.setWordWrap(True)
        rules_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        rules_text.setMinimumWidth(0)
        rules_text.setStyleSheet("color: #e0e7ff; font-size: 12px;")
        r_box_layout.addWidget(rules_text)
        atm_layout.addWidget(rules_box)

        self.results_layout.addWidget(atm_card)

        # 2. TACTICAL ADVICE CARD
        if result.tactical_advice:
            adv_card = QFrame()
            adv_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            adv_card.setMinimumWidth(0)
            adv_card.setStyleSheet("background-color: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 12px;")
            adv_layout = QVBoxLayout(adv_card)
            adv_layout.setSpacing(6)

            adv_header = QLabel("💡 Тактические советы для этого момента:")
            adv_header.setStyleSheet("color: #facc15; font-weight: bold; font-size: 12px;")
            adv_layout.addWidget(adv_header)

            for tip in result.tactical_advice:
                tip_label = QLabel(f"• {tip}")
                tip_label.setWordWrap(True)
                tip_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                tip_label.setMinimumWidth(0)
                tip_label.setStyleSheet("color: #f1f5f9; font-size: 12px; line-height: 1.4;")
                adv_layout.addWidget(tip_label)

            self.results_layout.addWidget(adv_card)

        # 3. DRAFT CRITIQUE (if applicable)
        if result.draft_critique:
            crit_card = QFrame()
            crit_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            crit_card.setMinimumWidth(0)
            crit_card.setStyleSheet("background-color: #3b0764; border: 1px solid #7e22ce; border-radius: 12px; padding: 12px;")
            crit_layout = QVBoxLayout(crit_card)
            crit_layout.setSpacing(6)

            crit_header = QLabel("🔍 Разбор твоего черновика:")
            crit_header.setStyleSheet("color: #f0abfc; font-weight: bold; font-size: 12px;")
            crit_layout.addWidget(crit_header)

            crit_body = QLabel(result.draft_critique)
            crit_body.setWordWrap(True)
            crit_body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            crit_body.setMinimumWidth(0)
            crit_body.setStyleSheet("color: #fae8ff; font-size: 12px; line-height: 1.3;")
            crit_layout.addWidget(crit_body)

            self.results_layout.addWidget(crit_card)

        # 4. ADAPTED REPLIES
        replies_title = QLabel("💬 Варианты твоего ответа (кликни для копирования):")
        replies_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; margin-top: 6px;")
        self.results_layout.addWidget(replies_title)

        for reply in result.adapted_replies:
            reply_card = self._create_reply_card(reply)
            self.results_layout.addWidget(reply_card)

        # Re-constrain scroll content to viewport width and prevent any horizontal overflow
        if self.scroll_area.widget():
            self.scroll_area.widget().setFixedWidth(self.scroll_area.viewport().width())
        self.scroll_area.horizontalScrollBar().setValue(0)

    def _create_reply_card(self, reply) -> QFrame:
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        card.setMinimumWidth(0)
        card.setStyleSheet("""
            QFrame {
                background-color: #172033;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame:hover {
                border: 1px solid #6366f1;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header: Style tag & Copy Button
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        style_badge = QLabel(reply.style)
        style_badge.setWordWrap(True)
        style_badge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        style_badge.setMinimumWidth(0)
        style_badge.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        top_row.addWidget(style_badge, 1)

        copy_btn = QPushButton("📋 Копировать")
        copy_btn.setFixedWidth(95)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: none;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4f46e5;
                color: #ffffff;
            }
        """)
        copy_btn.clicked.connect(lambda checked, text=reply.text, btn=copy_btn: self._copy_to_clipboard(text, btn))
        top_row.addWidget(copy_btn, 0)
        layout.addLayout(top_row)

        # Reply Text Box
        text_label = QLabel(reply.text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_label.setMinimumWidth(0)
        text_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            background-color: #0d1321;
            padding: 8px 10px;
            border-radius: 6px;
            line-height: 1.4;
        """)
        layout.addWidget(text_label)

        # Rationale
        if reply.rationale:
            rat_label = QLabel(f"💡 {reply.rationale}")
            rat_label.setWordWrap(True)
            rat_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            rat_label.setMinimumWidth(0)
            rat_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-style: italic;")
            layout.addWidget(rat_label)

        return card

    def _copy_to_clipboard(self, text: str, button: QPushButton):
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            original_text = button.text()
            button.setText("✓ Скопировано!")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            QTimer.singleShot(2000, lambda: self._reset_copy_button(button, original_text))

    def _reset_copy_button(self, button: QPushButton, text: str):
        button.setText(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4f46e5;
                color: #ffffff;
            }
        """)

    # --- Mouse Drag Support for Frameless Window ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        # Save position to config
        self.config["window_pos"] = [self.x(), self.y()]
        save_config(self.config)
