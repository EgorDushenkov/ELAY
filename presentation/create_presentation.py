import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette - Dark Minimalist
    BG_COLOR = RGBColor(11, 15, 25)         # Deep slate/black #0B0F19
    CARD_BG = RGBColor(24, 32, 47)          # Card container #18202F
    CARD_BORDER = RGBColor(46, 59, 82)      # Subtle border #2E3B52
    CARD_BG_ALT = RGBColor(30, 41, 59)      # Card active #1E293B

    ACCENT_INDIGO = RGBColor(99, 102, 241)  # #6366F1
    ACCENT_VIOLET = RGBColor(139, 92, 246)  # #8B5CF6
    ACCENT_CYAN = RGBColor(6, 182, 212)     # #06B6D4
    ACCENT_EMERALD = RGBColor(16, 185, 129) # #10B981
    ACCENT_AMBER = RGBColor(245, 158, 11)   # #F59E0B

    TEXT_TITLE = RGBColor(255, 255, 255)
    TEXT_BODY = RGBColor(203, 213, 225)     # #CBD5E1
    TEXT_MUTED = RGBColor(148, 163, 184)    # #94A3B8

    FONT_FAMILY = "Segoe UI"

    def apply_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()
        return bg

    def add_badge(slide, text, left, top, width=Inches(2.5), height=Inches(0.4), color=ACCENT_INDIGO):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(30, 27, 75) if color == ACCENT_INDIGO else RGBColor(19, 42, 38)
        shape.line.color.rgb = color
        shape.line.width = Pt(1)
        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = PP_ALIGN.CENTER
        p.font.name = FONT_FAMILY
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = color
        return shape

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # =========================================================================
    # SLIDE 1: ТИТУЛЬНЫЙ СЛАЙД
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_bg(s1)

    # Accent decorative glow line
    glow = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(0.9), Inches(10.9), Inches(0.04))
    glow.fill.solid()
    glow.fill.fore_color.rgb = ACCENT_INDIGO
    glow.line.fill.background()

    add_badge(s1, "HACKATHON SHOWCASE • AI ASSISTANT", Inches(1.2), Inches(1.2), Inches(3.6), Inches(0.38), ACCENT_CYAN)

    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        s1.shapes.add_picture(logo_path, Inches(1.2), Inches(1.85), width=Inches(1.2), height=Inches(1.2))

    # Title box
    tx1 = s1.shapes.add_textbox(Inches(2.6), Inches(1.65), Inches(9.5), Inches(1.6))
    tf1 = tx1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "VibeSense AI  (ELAY)"
    p1.font.name = FONT_FAMILY
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_TITLE

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Сервис, который «чувствует» эмоциональный окрас и контекст переписки"
    p1_sub.font.name = FONT_FAMILY
    p1_sub.font.size = Pt(17)
    p1_sub.font.bold = True
    p1_sub.font.color.rgb = ACCENT_INDIGO

    # Description Box
    desc_box = s1.shapes.add_textbox(Inches(1.2), Inches(3.4), Inches(10.9), Inches(1.2))
    tf_desc = desc_box.text_frame
    tf_desc.word_wrap = True
    p_desc = tf_desc.paragraphs[0]
    p_desc.text = (
        "Умный десктопный ассистент для Windows, который в реальном времени анализирует невербальные сигналы, "
        "скрытый подтекст и накал в любых мессенджерах, помогая сформулировать идеальный ответ под любую цель."
    )
    p_desc.font.name = FONT_FAMILY
    p_desc.font.size = Pt(14)
    p_desc.font.color.rgb = TEXT_BODY

    # 3 Info Cards at bottom
    features = [
        ("🪟 Windows Overlay (Alt+S)", "Работает поверх всех окон без переключения контекста"),
        ("🧠 Google Gemini 2.5 Flash", "Мультимодальный анализ визуальных скриншотов чата"),
        ("🛡️ Quota Shield (3.5 Lite)", "Умный fallback при исчерпании лимитов модели"),
    ]
    card_w = Inches(3.45)
    card_h = Inches(1.8)
    for i, (title, sub) in enumerate(features):
        cx = Inches(1.2) + i * Inches(3.72)
        add_card(s1, cx, Inches(4.85), card_w, card_h)
        tb = s1.shapes.add_textbox(cx + Inches(0.2), Inches(5.0), card_w - Inches(0.4), card_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_FAMILY
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_TITLE

        p_s = tf.add_paragraph()
        p_s.text = sub
        p_s.font.name = FONT_FAMILY
        p_s.font.size = Pt(11)
        p_s.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: ПРОБЛЕМА (ВВЕДЕНИЕ И БОЛЬ)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_bg(s2)

    add_badge(s2, "01 • ВВЕДЕНИЕ И ПРОБЛЕМА", Inches(1.2), Inches(0.8), Inches(3.0), Inches(0.38), ACCENT_AMBER)

    h2 = s2.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.2))
    tf2 = h2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Текст слеп: почему мы теряем 70% смысла в чатах?"
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(28)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_TITLE

    p2_sub = tf2.add_paragraph()
    p2_sub.text = "В цифровом общении отсутствуют интонация, мимика и взгляд. Люди видят лишь сухие буквы — и регулярно ошибаются в намерениях собеседника."
    p2_sub.font.name = FONT_FAMILY
    p2_sub.font.size = Pt(13)
    p2_sub.font.color.rgb = TEXT_MUTED

    problems = [
        (
            "🛑 Скрытая токсичность и сарказм",
            "Пассивная агрессия, скрытое недовольство или скрытый сарказм внешне выглядят нейтрально. Человек пропускает тревожные сигналы и теряет контроль над диалогом."
        ),
        (
            "⚡ Высокая цена одной фразы",
            "Одно неверно подобранное слово на Авито или FunPay мгновенно срывает выгодную сделку. Неудачный ответ коллеге или клиенту перерастает в затяжной конфликт."
        ),
        (
            "⏱️ Ступор перед экраном",
            "«Как отказать без обид?», «Как сторговаться и не выглядеть хамом?», «Как ответить девушке, не показавшись навязчивым?». Люди тратят десятки минут в сомнениях."
        ),
    ]

    pw = Inches(3.45)
    ph = Inches(3.8)
    for i, (title, desc) in enumerate(problems):
        px = Inches(1.2) + i * Inches(3.72)
        add_card(s2, px, Inches(2.7), pw, ph)

        # Indicator tag
        tag = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, px + Inches(0.3), Inches(2.95), Inches(0.4), Inches(0.05))
        tag.fill.solid()
        tag.fill.fore_color.rgb = ACCENT_AMBER
        tag.line.fill.background()

        tb = s2.shapes.add_textbox(px + Inches(0.25), Inches(3.2), pw - Inches(0.5), ph - Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(12)
        pd.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 3: ЦЕЛЕВАЯ АУДИТОРИЯ И СЦЕНАРИИ
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_bg(s3)

    add_badge(s3, "02 • ЦЕЛЕВАЯ АУДИТОРИЯ", Inches(1.2), Inches(0.8), Inches(2.8), Inches(0.38), ACCENT_CYAN)

    h3 = s3.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.1))
    tf3 = h3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "Кому и в каких ситуациях нужен VibeSense?"
    p3.font.name = FONT_FAMILY
    p3.font.size = Pt(28)
    p3.font.bold = True
    p3.font.color.rgb = TEXT_TITLE

    p3_sub = tf3.add_paragraph()
    p3_sub.text = "Инструмент незаменим везде, где исход переписки влияет на деньги, нервы или отношения:"
    p3_sub.font.name = FONT_FAMILY
    p3_sub.font.size = Pt(13)
    p3_sub.font.color.rgb = TEXT_MUTED

    audiences = [
        ("🤝 P2P-торговля и фриланс", "Авито, FunPay, Kwork, биржи услуг", "Позволяет получить лучшую цену, моментально распознать сомнительного покупателя или дожать сомневающегося клиента."),
        ("💼 Рабочие и деловые переписки", "Telegram, корпоративная почта, чаты команд", "Помогает ответить токсичному коллеге сухо и по фактам, сбить накал спора и не нарушить субординацию."),
        ("✨ Дейтинг и личное общение", "Сайты знакомств, VK, социальные сети", "Помогает считывать искренний интерес, выдерживать баланс значимости и поддерживать интригу без кринжа."),
        ("🛑 Трудные разговоры и личные границы", "Должники, родственники, требовательные заказчики", "Позволяет твёрдо сказать «нет», выставить личные границы без чувства вины и избежать манипуляций."),
    ]

    grid_w = Inches(5.3)
    grid_h = Inches(2.05)
    for i, (title, scope, text) in enumerate(audiences):
        row = i // 2
        col = i % 2
        gx = Inches(1.2) + col * Inches(5.6)
        gy = Inches(2.6) + row * Inches(2.25)

        add_card(s3, gx, gy, grid_w, grid_h)

        tb = s3.shapes.add_textbox(gx + Inches(0.3), gy + Inches(0.2), grid_w - Inches(0.6), grid_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        ps = tf.add_paragraph()
        ps.text = scope
        ps.font.name = FONT_FAMILY
        ps.font.size = Pt(11)
        ps.font.bold = True
        ps.font.color.rgb = ACCENT_CYAN

        pd = tf.add_paragraph()
        pd.text = text
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 4: ИДЕЯ И КОНЦЕПЦИЯ РЕШЕНИЯ
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_bg(s4)

    add_badge(s4, "03 • КОНЦЕПЦИЯ И ИДЕЯ", Inches(1.2), Inches(0.8), Inches(2.8), Inches(0.38), ACCENT_VIOLET)

    h4 = s4.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.1))
    tf4 = h4.text_frame
    tf4.word_wrap = True
    p4 = tf4.paragraphs[0]
    p4.text = "VibeSense AI: сервис, который «чувствует» переписку"
    p4.font.name = FONT_FAMILY
    p4.font.size = Pt(28)
    p4.font.bold = True
    p4.font.color.rgb = TEXT_TITLE

    p4_sub = tf4.add_paragraph()
    p4_sub.text = "Мы соединили мультимодальное зрение ИИ и поведенческую психологию в удобный оверлей поверх экрана:"
    p4_sub.font.name = FONT_FAMILY
    p4_sub.font.size = Pt(13)
    p4_sub.font.color.rgb = TEXT_MUTED

    pillars = [
        (
            "👁️ Визуальный контекст (Vision)",
            "Модель анализирует не голый скопированный текст, а скриншот живого интерфейса: расположение реплик, паузы между сообщениями, эмодзи, стикеры и реакции. Это возвращает те самые потерянные 70% невербалики.",
            ACCENT_CYAN
        ),
        (
            "📊 Оцифровка атмосферы чата",
            "ИИ вычисляет числовые метрики: шкалу напряжения (1–10), уровень формальности, социальную дистанцию и негласные правила именно этого чата (например: «здесь принято шутить», «точки в конце выглядят грубо»).",
            ACCENT_INDIGO
        ),
        (
            "🎯 Точная калибровка ответов",
            "Система берет ваш черновик (или пишет с нуля) и калибрует его под заданную цель: сбить агрессию, сторговаться, влиться в компанию или выставить жесткие границы в 1 клик.",
            ACCENT_EMERALD
        ),
    ]

    for i, (title, text, col_acc) in enumerate(pillars):
        px = Inches(1.2) + i * Inches(3.72)
        add_card(s4, px, Inches(2.65), pw, Inches(3.9))

        bar = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, px + Inches(0.3), Inches(2.9), Inches(0.5), Inches(0.06))
        bar.fill.solid()
        bar.fill.fore_color.rgb = col_acc
        bar.line.fill.background()

        tb = s4.shapes.add_textbox(px + Inches(0.3), Inches(3.15), pw - Inches(0.6), Inches(3.2))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        pd = tf.add_paragraph()
        pd.text = text
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(12)
        pd.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 5: КАК ЭТО РАБОТАЕТ (ПОЛЬЗОВАТЕЛЬСКИЙ СЦЕНАРИЙ)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_bg(s5)

    add_badge(s5, "04 • ПОЛЬЗОВАТЕЛЬСКИЙ СЦЕНАРИЙ", Inches(1.2), Inches(0.8), Inches(3.5), Inches(0.38), ACCENT_EMERALD)

    h5 = s5.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.1))
    tf5 = h5.text_frame
    tf5.word_wrap = True
    p5 = tf5.paragraphs[0]
    p5.text = "Мгновенный результат за 4 простых действия"
    p5.font.name = FONT_FAMILY
    p5.font.size = Pt(28)
    p5.font.bold = True
    p5.font.color.rgb = TEXT_TITLE

    p5_sub = tf5.add_paragraph()
    p5_sub.text = "Никаких копирований логов и переключений между окнами — ассистент прямо перед глазами:"
    p5_sub.font.name = FONT_FAMILY
    p5_sub.font.size = Pt(13)
    p5_sub.font.color.rgb = TEXT_MUTED

    steps = [
        ("01", "Alt + S", "Вызов оверлея", "Нажатие глобальной горячей клавиши мгновенно открывает стильное плавающее окно поверх любого мессенджера или сайта."),
        ("02", "📸 Снимок", "Захват экрана", "Нажатие кнопки активирует рамку выделения. Можно прикрепить до 10 кадров переписки подряд при прокрутке длинного чата."),
        ("03", "🎯 Цель", "Выбор стратегии", "Выберите готовый пресет (Сторговаться, Сбить накал, Влиться) или введите свою задачу словами (например, «вернуть долг»)."),
        ("04", "⚡ Ответ", "Вставка в 1 клик", "Через 1.5 сек модель выдает психологический разбор и 3–4 варианта ответов. Клик на карточку копирует текст для отправки."),
    ]

    sw = Inches(2.55)
    sh = Inches(4.0)
    for i, (num, tag, title, desc) in enumerate(steps):
        sx = Inches(1.2) + i * Inches(2.78)
        add_card(s5, sx, Inches(2.65), sw, sh)

        # Big Step Number
        num_box = s5.shapes.add_textbox(sx + Inches(0.2), Inches(2.8), Inches(1.2), Inches(0.6))
        ntf = num_box.text_frame
        ntf.margin_left = ntf.margin_top = 0
        np = ntf.paragraphs[0]
        np.text = num
        np.font.name = FONT_FAMILY
        np.font.size = Pt(22)
        np.font.bold = True
        np.font.color.rgb = ACCENT_EMERALD

        tb = s5.shapes.add_textbox(sx + Inches(0.2), Inches(3.45), sw - Inches(0.4), sh - Inches(0.9))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = tag
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        ps = tf.add_paragraph()
        ps.text = title
        ps.font.name = FONT_FAMILY
        ps.font.size = Pt(11)
        ps.font.bold = True
        ps.font.color.rgb = ACCENT_CYAN

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 6: КЛЮЧЕВОЙ ФУНКЦИОНАЛ
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    apply_bg(s6)

    add_badge(s6, "05 • КЛЮЧЕВЫЕ ВОЗМОЖНОСТИ", Inches(1.2), Inches(0.8), Inches(3.2), Inches(0.38), ACCENT_INDIGO)

    h6 = s6.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.1))
    tf6 = h6.text_frame
    tf6.word_wrap = True
    p6 = tf6.paragraphs[0]
    p6.text = "Что умеет ассистент под капотом?"
    p6.font.name = FONT_FAMILY
    p6.font.size = Pt(28)
    p6.font.bold = True
    p6.font.color.rgb = TEXT_TITLE

    p6_sub = tf6.add_paragraph()
    p6_sub.text = "Интеллектуальные инструменты для любого уровня сложности общения:"
    p6_sub.font.name = FONT_FAMILY
    p6_sub.font.size = Pt(13)
    p6_sub.font.color.rgb = TEXT_MUTED

    features_deep = [
        (
            "🎭 Детектор скрытого вайба и негласных правил",
            "Вычисляет шкалу накала / агрессии (от 1 до 10 с динамической цветовой индикацией), степень формальности общения и формулирует скрытые правила чата (например: «не душнить», «писать короткими репликами», «применять сарказм»).",
            ACCENT_AMBER
        ),
        (
            "✍️ Аудит черновика и адаптивные стили ответов",
            "Если вы ввели черновик (например: «го за 500»), ИИ разберет его слабые стороны и перепишет в 3–4 различных стилях: дипломатичном, твердом, дружелюбном или компромиссном — с объяснением психологического эффекта каждой фразы.",
            ACCENT_CYAN
        ),
        (
            "🛡️ Двойная модель с Auto-Fallback (Quota Shield)",
            "В шапке доступен выбор модели: Gemini 2.5 Flash (основная) и 3.5 Flash Lite (резервная). При исчерпании суточной квоты запросов программа сама бесшовно переключает модель, не прерывая рабочий процесс пользователя.",
            ACCENT_EMERALD
        ),
    ]

    f_w = Inches(10.9)
    f_h = Inches(1.18)
    for i, (title, desc, acc) in enumerate(features_deep):
        fy = Inches(2.65) + i * Inches(1.4)
        add_card(s6, Inches(1.2), fy, f_w, f_h)

        # Left Accent bar
        bar = s6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), fy, Inches(0.12), f_h)
        bar.fill.solid()
        bar.fill.fore_color.rgb = acc
        bar.line.fill.background()

        tb = s6.shapes.add_textbox(Inches(1.5), fy + Inches(0.12), f_w - Inches(0.5), f_h - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 7: ТЕХНИЧЕСКАЯ ЧАСТЬ (ПРОСТО О СЛОЖНОМ)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    apply_bg(s7)

    add_badge(s7, "06 • ТЕХНИЧЕСКАЯ АРХИТЕКТУРА", Inches(1.2), Inches(0.8), Inches(3.5), Inches(0.38), ACCENT_CYAN)

    h7 = s7.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.1))
    tf7 = h7.text_frame
    tf7.word_wrap = True
    p7 = tf7.paragraphs[0]
    p7.text = "Техническая основа: надежно, быстро и безопасно"
    p7.font.name = FONT_FAMILY
    p7.font.size = Pt(28)
    p7.font.bold = True
    p7.font.color.rgb = TEXT_TITLE

    p7_sub = tf7.add_paragraph()
    p7_sub.text = "Стек современных технологий, гарантирующий плавную работу без фризов:"
    p7_sub.font.name = FONT_FAMILY
    p7_sub.font.size = Pt(13)
    p7_sub.font.color.rgb = TEXT_MUTED

    tech_cards = [
        ("🖥️ PyQt6 Frameless UI", "Плавающий оверлей с блокировкой скролла", "Кастомный компонент FitScrollArea принудительно исключает горизонтальный сдвиг. Поддержка High-DPI экранов (125%, 150%, 200%) и минимизация в трей Windows."),
        ("🧠 Gemini Multimodal & Pydantic", "Визуальные токены и строгий JSON", "Скриншоты диалога отправляются напрямую в мультимодальную модель Google Gemini через Structured Output. Pydantic v2 гарантирует 100% валидный формат ответа."),
        ("🔒 Безопасность и антифрод", "Полная конфиденциальность данных", "Захват происходит исключительно через системный экранный буфер Windows (QBuffer) без записи файлов на диск. Никаких токенов или юзерботов — 0% риска бана в Telegram."),
        ("📦 Standalone Portable EXE", "Запуск из одного клика (70 МБ)", "Собран через PyInstaller в единый бинарник со встроенными библиотеками, иконкой и API-ключом («Zero-Config»). Не требует установки Python или сторонних зависимостей."),
    ]

    for i, (title, sub, text) in enumerate(tech_cards):
        row = i // 2
        col = i % 2
        gx = Inches(1.2) + col * Inches(5.6)
        gy = Inches(2.65) + row * Inches(2.2)

        add_card(s7, gx, gy, grid_w, Inches(2.0))

        tb = s7.shapes.add_textbox(gx + Inches(0.3), gy + Inches(0.18), grid_w - Inches(0.6), Inches(1.7))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(15)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.name = FONT_FAMILY
        ps.font.size = Pt(11)
        ps.font.bold = True
        ps.font.color.rgb = ACCENT_INDIGO

        pd = tf.add_paragraph()
        pd.text = text
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 8: ЗАКЛЮЧЕНИЕ И ИТОГИ
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    apply_bg(s8)

    add_badge(s8, "07 • ЗАКЛЮЧЕНИЕ И ИТОГИ", Inches(1.2), Inches(0.8), Inches(3.0), Inches(0.38), ACCENT_EMERALD)

    h8 = s8.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.1))
    tf8 = h8.text_frame
    tf8.word_wrap = True
    p8 = tf8.paragraphs[0]
    p8.text = "VibeSense AI: уверенность в каждом сообщении"
    p8.font.name = FONT_FAMILY
    p8.font.size = Pt(28)
    p8.font.bold = True
    p8.font.color.rgb = TEXT_TITLE

    p8_sub = tf8.add_paragraph()
    p8_sub.text = "Проект превращает невербальный хаос переписок в понятный, предсказуемый и управляемый диалог."
    p8_sub.font.name = FONT_FAMILY
    p8_sub.font.size = Pt(13)
    p8_sub.font.color.rgb = TEXT_MUTED

    # 3 Big Stat Cards
    stats = [
        ("< 2 сек", "Мгновенный анализ", "От снимка экрана до готовых вариантов идеального ответа"),
        ("100%", "Совместимость", "Работает в Telegram, Discord, WhatsApp, браузере и играх"),
        ("0 квот", "Отказоустойчивость", "Двойная модель: 2.5 Flash + автоматический 3.5 Flash Lite"),
    ]

    stat_w = Inches(3.45)
    stat_h = Inches(2.2)
    for i, (num, lbl, sub) in enumerate(stats):
        sx = Inches(1.2) + i * Inches(3.72)
        add_card(s8, sx, Inches(2.6), stat_w, stat_h)

        tb = s8.shapes.add_textbox(sx + Inches(0.2), Inches(2.75), stat_w - Inches(0.4), stat_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True

        pn = tf.paragraphs[0]
        pn.text = num
        pn.font.name = FONT_FAMILY
        pn.font.size = Pt(32)
        pn.font.bold = True
        pn.font.color.rgb = ACCENT_EMERALD

        pl = tf.add_paragraph()
        pl.text = lbl
        pl.font.name = FONT_FAMILY
        pl.font.size = Pt(14)
        pl.font.bold = True
        pl.font.color.rgb = TEXT_TITLE

        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.name = FONT_FAMILY
        ps.font.size = Pt(11)
        ps.font.color.rgb = TEXT_MUTED

    # Bottom Callout Link Card
    callout = add_card(s8, Inches(1.2), Inches(5.15), Inches(10.9), Inches(1.6), CARD_BG_ALT, ACCENT_INDIGO)
    ctb = s8.shapes.add_textbox(Inches(1.5), Inches(5.25), Inches(10.3), Inches(1.4))
    ctf = ctb.text_frame
    ctf.word_wrap = True

    cp1 = ctf.paragraphs[0]
    cp1.text = "🚀 Открытый код и готовый бинарник доступны на GitHub:"
    cp1.font.name = FONT_FAMILY
    cp1.font.size = Pt(15)
    cp1.font.bold = True
    cp1.font.color.rgb = TEXT_TITLE

    cp2 = ctf.add_paragraph()
    cp2.text = "• Репозиторий:  https://github.com/EgorDushenkov/ELAY"
    cp2.font.name = FONT_FAMILY
    cp2.font.size = Pt(12)
    cp2.font.bold = True
    cp2.font.color.rgb = ACCENT_CYAN

    cp3 = ctf.add_paragraph()
    cp3.text = "• Скачать VibeSense.exe:  https://github.com/EgorDushenkov/ELAY/releases/tag/v1.0.0"
    cp3.font.name = FONT_FAMILY
    cp3.font.size = Pt(12)
    cp3.font.bold = True
    cp3.font.color.rgb = ACCENT_EMERALD

    # Output file
    out_path = os.path.join(os.path.dirname(__file__), "VibeSense_AI_Presentation.pptx")
    prs.save(out_path)
    print(f"SUCCESS: Presentation saved to {out_path}")

if __name__ == "__main__":
    create_deck()
