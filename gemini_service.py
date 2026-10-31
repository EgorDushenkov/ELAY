import json
import io
from typing import List, Optional, Tuple, Union
from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class Atmosphere(BaseModel):
    vibe: str = Field(description="Краткая и емкая характеристика вайба (например: 'Холодно-настороженный', 'Токсично-ироничный', 'Теплый приятельский')")
    tension_score: int = Field(description="Уровень накала / напряжения от 1 (полный релакс и дружелюбие) до 10 (открытый конфликт, агрессия, ультиматумы)")
    formality_score: int = Field(description="Уровень формальности от 1 (интернет-сленг, мемчики, панибратство) до 10 (строгий протокол, юридический тон)")
    social_distance: str = Field(description="Дистанция между участниками (например: 'Близкие друзья', 'Настороженные незнакомцы', 'Клиент и продавец')")
    pace_and_rhythm: str = Field(description="Темп и формат (например: 'Быстрый пинг-понг короткими репликами', 'Затяжные паузы, односложные ответы')")
    unspoken_rules: str = Field(description="Негласные законы этого чата (например: 'Не ставить точку в конце', 'Никаких смайлов-скобочек', 'Отвечать строго по фактам')")

class AdaptedReply(BaseModel):
    style: str = Field(description="Название стиля ответа (например: '⚡ Вайбовый (свой в доску)', '🛡️ Уверенно-вежливый', '🤝 Выгодный торг', '✨ Ироничный')")
    text: str = Field(description="Сам готовый текст сообщения для отправки")
    rationale: str = Field(description="Почему эта реплика сработает и как повлияет на собеседника")

class ChatAnalysisResult(BaseModel):
    summary: str = Field(description="Краткая суть происходящего в переписке на скриншоте (в 1-2 предложениях)")
    atmosphere: Atmosphere
    tactical_advice: List[str] = Field(description="2-4 острых практических совета: что сейчас сработает, а что вызовет отторжение/кринж")
    draft_critique: Optional[str] = Field(default=None, description="Если был передан черновик: анализ того, как его воспримет собеседник и какие в нем ошибки")
    adapted_replies: List[AdaptedReply] = Field(description="3-4 адаптированных варианта ответа")


SYSTEM_INSTRUCTION = """Ты — первоклассный эксперт по цифровой прагматике, психологии онлайн-коммуникации, микро-сигналам и нетикету.
Тебе предоставлен скриншот фрагмента переписки из мессенджера или сервиса (Telegram, Discord, WhatsApp, FunPay, Авито, VK, Tinder, корпоративный чат, форум и т.д.).

ТВОЯ ЗАДАЧА:
1. Внимательно проанализировать визуальный контекст:
   - Расположение сообщений (слева — собеседник, справа — пользователь, либо по именам/аватаркам).
   - Интонации, скрытые смыслы, пассивную агрессию, сарказм, холодность или тепло.
   - Невербалику: таймстампы (задержки), размер баблов, знаки препинания (точки, восклицания, отсутствие знаков, скобочки), эмодзи.
2. Определить эмоциональную окраску, накал (1-10) и формальность (1-10).
3. Сформулировать негласные правила и тактические советы для пользователя в этой ситуации.
4. Сгенерировать варианты ответа:
   - Если пользователь передал свой черновик: обязательно разбери его, укажи на слабые места, и перепиши под выбранную цель так, чтобы сохранить факты и смысл, но идеально откалибровать тональность.
   - Если черновик не передан: предложи 3-4 сильных варианта реплики под выбранную цель, которые идеально лягут в динамику этой беседы.

Тексты ответов должны звучать максимально естественно для живого человека на русском языке (без роботоподобных клише)."""


class GeminiChatAnalyzer:
    """Service wrapper for Google Gemini Flash multimodal API."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key.strip()
        self.model_name = model_name
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if not self.api_key:
            raise ValueError("API-ключ Gemini не указан! Укажите его в настройках приложения или в файле .env.")
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def update_credentials(self, api_key: str, model_name: Optional[str] = None):
        self.api_key = api_key.strip()
        if model_name:
            self.model_name = model_name
        self._client = None

    def test_connection(self) -> Tuple[bool, str]:
        """Tests the API key with a minimal request."""
        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents="Ответь одним словом: 'Работает'",
            )
            return True, response.text.strip()
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err or "400" in err:
                return False, "Неверный API ключ (API_KEY_INVALID). Проверьте правильность ключа."
            elif "PERMISSION_DENIED" in err or "403" in err:
                return False, "Доступ запрещен (403). Проверьте права ключа в Google AI Studio."
            elif "RESOURCE_EXHAUSTED" in err or "429" in err:
                return False, "Превышен лимит запросов (429 Rate Limit). Подождите минуту."
            return False, f"Ошибка: {err}"

    def analyze_chat(
        self,
        images: Union[List[Image.Image], Image.Image],
        goal_title: str,
        goal_instruction: str,
        draft_reply: str = "",
    ) -> ChatAnalysisResult:
        """
        Sends the screenshot(s) and user intent to Gemini Flash with structured JSON output.
        Supports up to 10 screenshots analyzed chronologically as one dialogue.
        """
        client = self._get_client()

        if isinstance(images, Image.Image):
            images = [images]
        if not images:
            raise ValueError("Не добавлено ни одного скриншота для анализа!")

        # Prepare multimodal content parts
        contents = []
        for i, img in enumerate(images, 1):
            img_buffer = io.BytesIO()
            if img.mode in ("RGBA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                rgb_img.save(img_buffer, format="JPEG", quality=85)
            else:
                img.save(img_buffer, format="JPEG", quality=85)

            if len(images) > 1:
                contents.append(f"--- СКРИНШОТ #{i} (из {len(images)}) ---")
            contents.append(types.Part.from_bytes(data=img_buffer.getvalue(), mime_type="image/jpeg"))

        # Build prompt instructions
        prompt_parts = []
        if len(images) > 1:
            prompt_parts.append(
                f"КОНТЕКСТ: Пользователь предоставил серию из {len(images)} последовательных скриншотов диалога. "
                "Проанализируй динамику всей цепочки сообщений целиком, учитывая развитие разговора от первого скриншота к последнему."
            )

        prompt_parts.extend([
            f"ЦЕЛЬ ПОЛЬЗОВАТЕЛЯ ДЛЯ ЭТОГО ОТВЕТА: {goal_title}",
            f"ИНСТРУКЦИЯ К ЦЕЛИ: {goal_instruction}",
        ])

        if draft_reply.strip():
            prompt_parts.append(
                f"ЧЕРНОВИК ПОЛЬЗОВАТЕЛЯ: \"{draft_reply.strip()}\"\n"
                f"(Обязательно проанализируй этот черновик в поле draft_critique и предложи адаптированные версии в adapted_replies, сохраняя факты, но меняя подачу под вайб чата)."
            )
        else:
            prompt_parts.append(
                "Черновик ответа не указан. Предложи лучшие варианты ответа под контекст ситуации и выбранную цель."
            )

        user_prompt_text = "\n\n".join(prompt_parts)
        contents.append(user_prompt_text)

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ChatAnalysisResult,
            temperature=0.7,
        )

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            # In google-genai with response_schema, response.parsed contains the Pydantic instance directly!
            if hasattr(response, "parsed") and response.parsed:
                return response.parsed

            # Fallback parse from response.text
            data = json.loads(response.text)
            return ChatAnalysisResult(**data)

        except Exception as e:
            err_msg = str(e)
            print(f"[Gemini Error]: {err_msg}")
            # If 2.5-flash encounters an issue (rate limit, quota exhausted, 429), auto-fallback to 3.5-flash-lite
            is_quota_or_limit = any(x in err_msg.lower() for x in ["429", "resource_exhausted", "quota", "limit", "rate"])
            if (is_quota_or_limit or "model" in err_msg.lower()) and self.model_name == "gemini-2.5-flash":
                try:
                    print("[Gemini] Limit/quota reached on 2.5-flash, auto-switching to gemini-3.5-flash-lite...")
                    fallback_response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=contents,
                        config=config,
                    )
                    if hasattr(fallback_response, "parsed") and fallback_response.parsed:
                        res = fallback_response.parsed
                        res.summary = f"⚡ [3.5 Flash Lite: авто-переход по лимиту] {res.summary}"
                        return res
                    data = json.loads(fallback_response.text)
                    res = ChatAnalysisResult(**data)
                    res.summary = f"⚡ [3.5 Flash Lite: авто-переход по лимиту] {res.summary}"
                    return res
                except Exception as fb_err:
                    print(f"[Gemini Fallback Error]: {fb_err}")
            raise e

