import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

CONFIG_FILE = APP_DIR / "config.json"
ENV_FILE = APP_DIR / ".env"

load_dotenv(ENV_FILE)
EMBEDDED_API_KEY = os.getenv("GEMINI_API_KEY", "")

DEFAULT_CONFIG = {
    "gemini_api_key": EMBEDDED_API_KEY,
    "model_name": "gemini-2.5-flash",
    "hotkey": "alt+s",
    "prompt_goal": "Влиться в беседу",
    "window_pos": None,
}

# Available models
AVAILABLE_MODELS = [
    {
        "id": "gemini-2.5-flash",
        "label": "⚡ Gemini 2.5 Flash (Основная)",
        "desc": "Высокое качество анализа (по умолчанию)"
    },
    {
        "id": "gemini-3.5-flash-lite",
        "label": "🚀 Gemini 3.5 Flash Lite (Запасная)",
        "desc": "Быстрая модель на случай исчерпания квоты 2.5 Flash"
    }
]

# Pre-defined goals/presets
GOAL_PRESETS = [
    {
        "id": "blend_in",
        "label": "⚡ Влиться в беседу",
        "instruction": "Помоги стать 'своим в доске'. Скопируй стиль, лексику, длину фраз и уровень юмора чата.",
    },
    {
        "id": "cool_down",
        "label": "🛡️ Сбить накал / Разрядить",
        "instruction": "Собеседник агрессивен или напряжен. Помоги тактично снизить градус, избежать эскалации и погасить конфликт без унижения своего достоинства.",
    },
    {
        "id": "bargain",
        "label": "🤝 Сторговаться (Авито / FunPay)",
        "instruction": "Торговля или деловой чат на бирже/маркетплейсе. Помоги получить лучшую цену или условия, оставаясь вежливым, но непоколебимым.",
    },
    {
        "id": "flirt",
        "label": "✨ Флирт & Симпатия",
        "instruction": "Романтическое общение. Добавь легкой иронии, заинтересованности и интриги, сохраняя баланс значимости без навязчивости.",
    },
    {
        "id": "firm_boundary",
        "label": "🛑 Твердые границы / Отказ",
        "instruction": "Нужно четко и уверенно сказать 'нет' или поставить рамки без лишних оправданий и без грубости.",
    },
    {
        "id": "business",
        "label": "💼 Строго по делу",
        "instruction": "Максимально лаконично, структурированно, без воды и лишних эмоций, по стандартам делового этикета.",
    },
]

def load_config() -> dict:
    """Loads configuration with embedded key fallback."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)

    config = dict(DEFAULT_CONFIG)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] Error loading config.json: {e}")

    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        config["gemini_api_key"] = env_key.strip()
    elif not config.get("gemini_api_key"):
        config["gemini_api_key"] = EMBEDDED_API_KEY

    return config

def save_config(config_data: dict) -> bool:
    """Saves updated config to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Config] Error saving config.json: {e}")
        return False
