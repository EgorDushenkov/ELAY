import os
import sys
import unittest
from PIL import Image

# Set offscreen Qt platform for headless testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from config import load_config, save_config, GOAL_PRESETS
from gemini_service import ChatAnalysisResult, Atmosphere, AdaptedReply
from chat_overlay import FloatingOverlayWindow
from snipper import SnippingWidget
from settings_dialog import SettingsDialog


class TestVibeSense(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_config(self):
        cfg = load_config()
        self.assertIn("gemini_api_key", cfg)
        self.assertIn("model_name", cfg)
        self.assertIn("hotkey", cfg)
        self.assertGreater(len(GOAL_PRESETS), 0)

    def test_pydantic_schema(self):
        data = {
            "summary": "Покупатель на FunPay интересуется товаром и торгуется",
            "atmosphere": {
                "vibe": "Деловой с нотками недоверия",
                "tension_score": 4,
                "formality_score": 5,
                "social_distance": "Незнакомцы на торговой площадке",
                "pace_and_rhythm": "Короткие реплики, быстрые ответы",
                "unspoken_rules": "Не хамить, не занижать цену более чем на 20%, подтверждать наличие"
            },
            "tactical_advice": [
                "Не соглашайся на первую скидку сразу",
                "Отвечай четко без лишних приветствий"
            ],
            "draft_critique": "Слишком много оправданий в черновике",
            "adapted_replies": [
                {
                    "style": "🤝 Твердая позиция",
                    "text": "Могу скинуть максимум 100 руб, если заберешь прямо сейчас.",
                    "rationale": "Создает дефицит времени и фиксирует цену."
                }
            ]
        }
        res = ChatAnalysisResult(**data)
        self.assertEqual(res.atmosphere.tension_score, 4)
        self.assertEqual(len(res.adapted_replies), 1)

    def test_overlay_ui_instantiation(self):
        overlay = FloatingOverlayWindow()
        self.assertIsNotNone(overlay)
        self.assertEqual(overlay.model_combo.count(), 2)
        self.assertEqual(overlay.model_combo.itemData(0), "gemini-2.5-flash")
        self.assertEqual(overlay.model_combo.itemData(1), "gemini-3.5-flash-lite")

        # Test adding synthetic images
        test_img = Image.new("RGB", (600, 400), color=(30, 40, 60))
        overlay.add_captured_image(test_img)
        self.assertEqual(len(overlay.captured_images), 1)

        # Test adding up to 10 images
        for _ in range(3):
            overlay.add_captured_image(test_img)
        self.assertEqual(len(overlay.captured_images), 4)

        # Test custom goal input
        overlay.custom_goal_edit.setText("Попросить вернуть долг без скандала")
        self.assertEqual(overlay.custom_goal_edit.text(), "Попросить вернуть долг без скандала")
        # Preset buttons should be deselected
        for btn in overlay.preset_buttons:
            self.assertFalse(btn.isChecked())

        # Test clicking preset clears custom goal
        overlay._select_preset(2)
        self.assertEqual(overlay.custom_goal_edit.text(), "")
        self.assertTrue(overlay.preset_buttons[2].isChecked())

        # Test rendering results
        dummy_result = ChatAnalysisResult(
            summary="Дружеский стеб в Discord " * 10,
            atmosphere=Atmosphere(
                vibe="Иронично-приятельский вайб с глубоким подтекстом и сарказмом " * 5,
                tension_score=2,
                formality_score=1,
                social_distance="Близкие знакомые, общаются каждый день " * 4,
                pace_and_rhythm="Пинг-понг мемами и быстрыми репликами " * 4,
                unspoken_rules="Точки в конце не ставить, писать коротко, не душнить " * 5
            ),
            tactical_advice=["Ответь зеркальным сарказмом " * 5],
            adapted_replies=[
                AdaptedReply(
                    style="⚡ Вайбовый стиль свой в доску с нотками иронии и подкола " * 3,
                    text="хаха да конечно, держи карман шире. " * 20,
                    rationale="Поддерживает неформальный стеб и снимает напряжение в чате. " * 5
                )
            ]
        )
        overlay._render_results(dummy_result)
        # Check that results widgets were added
        self.assertGreater(overlay.results_layout.count(), 0)
        # Verify horizontal scroll is strictly 0 (no horizontal overflow)
        self.assertEqual(overlay.scroll_area.horizontalScrollBar().maximum(), 0)

    def test_snipper_to_pil(self):
        from PyQt6.QtGui import QPixmap, QColor
        snipper = SnippingWidget()
        pm = QPixmap(200, 150)
        pm.fill(QColor("blue"))
        img = snipper._pixmap_to_pil(pm)
        self.assertEqual(img.size, (200, 150))

    def test_multi_image_gemini_interface(self):
        from gemini_service import GeminiChatAnalyzer
        analyzer = GeminiChatAnalyzer(api_key="test_dummy_key")
        # Should raise on empty images
        with self.assertRaises(ValueError):
            analyzer.analyze_chat(images=[], goal_title="Test", goal_instruction="Test")

    def test_settings_dialog_instantiation(self):
        dialog = SettingsDialog()
        self.assertIsNotNone(dialog)
        self.assertGreater(dialog.model_combo.count(), 0)


if __name__ == "__main__":
    unittest.main()

