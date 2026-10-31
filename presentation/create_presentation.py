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

    # Minimalist Dark Palette
    BG_COLOR = RGBColor(11, 15, 25)         # Deep slate/black #0B0F19
    CARD_BG = RGBColor(22, 30, 44)          # Card container #161E2C
    CARD_BORDER = RGBColor(46, 59, 82)      # Subtle border #2E3B52
    CARD_BG_ALT = RGBColor(28, 38, 56)      # Active card #1C2638

    ACCENT_INDIGO = RGBColor(99, 102, 241)  # #6366F1
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

    def add_badge(slide, text, left, top, width=Inches(2.4), height=Inches(0.36), color=ACCENT_INDIGO):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(26, 28, 50) if color == ACCENT_INDIGO else RGBColor(16, 36, 34)
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

    # Accent decorative top line
    glow = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(0.9), Inches(10.9), Inches(0.04))
    glow.fill.solid()
    glow.fill.fore_color.rgb = ACCENT_INDIGO
    glow.line.fill.background()

    add_badge(s1, "ПРОЕКТ НА КОНКУРС • AI ASSISTANT", Inches(1.2), Inches(1.2), Inches(3.4), Inches(0.38), ACCENT_CYAN)

    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        s1.shapes.add_picture(logo_path, Inches(1.2), Inches(1.85), width=Inches(1.25), height=Inches(1.25))

    tx1 = s1.shapes.add_textbox(Inches(2.65), Inches(1.65), Inches(9.4), Inches(1.6))
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

    desc_box = s1.shapes.add_textbox(Inches(1.2), Inches(3.4), Inches(10.9), Inches(1.1))
    tf_desc = desc_box.text_frame
    tf_desc.word_wrap = True
    p_desc = tf_desc.paragraphs[0]
    p_desc.text = (
        "Умный десктопный ассистент для Windows: анализирует скрытый подтекст диалогов в любых мессенджерах "
        "и помогает сформулировать идеальный ответ под конкретную цель."
    )
    p_desc.font.name = FONT_FAMILY
    p_desc.font.size = Pt(14)
    p_desc.font.color.rgb = TEXT_BODY

    features = [
        ("🪟 Плавающий оверлей", "Вызывается по Alt+S поверх любых чатов и окон без переключения контекста"),
        ("🧠 Нейросетевой анализ", "Мультимодальное зрение по API: видит реальный интерфейс переписки"),
        ("⚡ Готов к работе (.exe)", "Автономный запуск в один клик без установки дополнительного софта"),
    ]
    card_w = Inches(3.45)
    card_h = Inches(1.75)
    for i, (title, sub) in enumerate(features):
        cx = Inches(1.2) + i * Inches(3.72)
        add_card(s1, cx, Inches(4.85), card_w, card_h)
        tb = s1.shapes.add_textbox(cx + Inches(0.2), Inches(5.0), card_w - Inches(0.4), card_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.name = FONT_FAMILY
        ps.font.size = Pt(11)
        ps.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: ОТ ПРОБЛЕМЫ К ИДЕЕ
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    apply_bg(s2)

    add_badge(s2, "01 • ОТ ПРОБЛЕМЫ К ИДЕЕ", Inches(1.2), Inches(0.8), Inches(2.9), Inches(0.38), ACCENT_AMBER)

    h2 = s2.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.0))
    tf2 = h2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = "Почему текст обманчив и как это решает VibeSense?"
    p2.font.name = FONT_FAMILY
    p2.font.size = Pt(28)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_TITLE

    p2_sub = tf2.add_paragraph()
    p2_sub.text = "В цифровом общении теряется невербалика: интонации, паузы и мимика. Человек видит только сухие буквы."
    p2_sub.font.name = FONT_FAMILY
    p2_sub.font.size = Pt(13)
    p2_sub.font.color.rgb = TEXT_MUTED

    # Two large columns: Problem vs Idea
    col_w = Inches(5.3)
    col_h = Inches(4.3)

    # Column Left: Problem
    add_card(s2, Inches(1.2), Inches(2.55), col_w, col_h)
    bar_left = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(2.55), Inches(0.1), col_h)
    bar_left.fill.solid()
    bar_left.fill.fore_color.rgb = ACCENT_AMBER
    bar_left.line.fill.background()

    tb_prob = s2.shapes.add_textbox(Inches(1.5), Inches(2.75), col_w - Inches(0.5), col_h - Inches(0.4))
    tf_p = tb_prob.text_frame
    tf_p.word_wrap = True

    tp = tf_p.paragraphs[0]
    tp.text = "🛑 Проблема цифрового текста"
    tp.font.name = FONT_FAMILY
    tp.font.size = Pt(17)
    tp.font.bold = True
    tp.font.color.rgb = TEXT_TITLE

    prob_points = [
        ("• Скрытая агрессия и сарказм: ", "пассивный негатив часто прячется за вежливыми фразами — пропустить его легко."),
        ("• Цена ошибки в один ответ: ", "сорванная сделка на Авито/FunPay, конфликт с клиентом или ссора в рабочем чате."),
        ("• Ступор формулировок: ", "поиск ответа отнимает десятки минут: «как отказать без обид?», «как поторговаться?»."),
    ]
    for bold_txt, norm_txt in prob_points:
        p_item = tf_p.add_paragraph()
        p_item.font.name = FONT_FAMILY
        p_item.font.size = Pt(12)
        run_b = p_item.add_run()
        run_b.text = bold_txt
        run_b.font.bold = True
        run_b.font.color.rgb = ACCENT_AMBER
        run_n = p_item.add_run()
        run_n.text = norm_txt
        run_n.font.color.rgb = TEXT_BODY

    # Column Right: Solution
    add_card(s2, Inches(6.8), Inches(2.55), col_w, col_h)
    bar_right = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(2.55), Inches(0.1), col_h)
    bar_right.fill.solid()
    bar_right.fill.fore_color.rgb = ACCENT_EMERALD
    bar_right.line.fill.background()

    tb_sol = s2.shapes.add_textbox(Inches(7.1), Inches(2.75), col_w - Inches(0.5), col_h - Inches(0.4))
    tf_s = tb_sol.text_frame
    tf_s.word_wrap = True

    ts = tf_s.paragraphs[0]
    ts.text = "✨ Идея решения: VibeSense AI"
    ts.font.name = FONT_FAMILY
    ts.font.size = Pt(17)
    ts.font.bold = True
    ts.font.color.rgb = TEXT_TITLE

    sol_points = [
        ("• «Чувствует» живой контекст: ", "анализирует скриншот чата (таймстампы, паузы, реакции, эмодзи), а не сухой текст."),
        ("• Оцифровывает атмосферу: ", "шкала накала (1–10), уровень формальности и негласные правила именно этого чата."),
        ("• Помогает в любых сферах: ", "P2P-торговля (сбить цену), рабочие чаты (снять накал), дейтинг и защита личных границ."),
    ]
    for bold_txt, norm_txt in sol_points:
        p_item = tf_s.add_paragraph()
        p_item.font.name = FONT_FAMILY
        p_item.font.size = Pt(12)
        run_b = p_item.add_run()
        run_b.text = bold_txt
        run_b.font.bold = True
        run_b.font.color.rgb = ACCENT_EMERALD
        run_n = p_item.add_run()
        run_n.text = norm_txt
        run_n.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 3: ПОЛЬЗОВАТЕЛЬСКИЙ СЦЕНАРИЙ И ФУНКЦИОНАЛ
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    apply_bg(s3)

    add_badge(s3, "02 • СЦЕНАРИЙ И ВОЗМОЖНОСТИ", Inches(1.2), Inches(0.8), Inches(3.4), Inches(0.38), ACCENT_CYAN)

    h3 = s3.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.0))
    tf3 = h3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = "Как работает сервис: от скриншота к готовому ответу"
    p3.font.name = FONT_FAMILY
    p3.font.size = Pt(28)
    p3.font.bold = True
    p3.font.color.rgb = TEXT_TITLE

    p3_sub = tf3.add_paragraph()
    p3_sub.text = "Быстрый цикл работы прямо во время переписки (занимает менее 2 секунд):"
    p3_sub.font.name = FONT_FAMILY
    p3_sub.font.size = Pt(13)
    p3_sub.font.color.rgb = TEXT_MUTED

    # 4 Steps Horizontal Cards
    steps = [
        ("01", "Alt + S", "Открытие плавающего окна поверх любого мессенджера"),
        ("02", "Снимок", "Выделение области чата (до 10 скриншотов подряд)"),
        ("03", "Цель", "Выбор пресета (Торг, Накал, Влиться) или свой текст"),
        ("04", "1 клик", "Готовый ответ копируется в буфер обмена для вставки"),
    ]
    sw = Inches(2.55)
    sh = Inches(1.9)
    for i, (num, tag, desc) in enumerate(steps):
        sx = Inches(1.2) + i * Inches(2.78)
        add_card(s3, sx, Inches(2.55), sw, sh)

        tb = s3.shapes.add_textbox(sx + Inches(0.2), Inches(2.7), sw - Inches(0.4), sh - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = f"{num} • {tag}"
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = ACCENT_CYAN

        pd = tf.add_paragraph()
        pd.text = desc
        pd.font.name = FONT_FAMILY
        pd.font.size = Pt(11)
        pd.font.color.rgb = TEXT_BODY

    # 2 Feature Bottom Cards
    feat_w = Inches(5.3)
    feat_h = Inches(2.05)

    add_card(s3, Inches(1.2), Inches(4.75), feat_w, feat_h)
    tb_f1 = s3.shapes.add_textbox(Inches(1.4), Inches(4.9), feat_w - Inches(0.4), feat_h - Inches(0.3))
    tff1 = tb_f1.text_frame
    tff1.word_wrap = True
    pf1_t = tff1.paragraphs[0]
    pf1_t.text = "🎭 Анализ атмосферы и негласных правил"
    pf1_t.font.name = FONT_FAMILY
    pf1_t.font.size = Pt(14)
    pf1_t.font.bold = True
    pf1_t.font.color.rgb = TEXT_TITLE

    pf1_d = tff1.add_paragraph()
    pf1_d.text = (
        "Модель оценивает накал (1–10 с цветовой индикацией), дистанцию и скрытые законы чата "
        "(например: «не душнить», «писать коротко», «сарказм уместен»)."
    )
    pf1_d.font.name = FONT_FAMILY
    pf1_d.font.size = Pt(11)
    pf1_d.font.color.rgb = TEXT_BODY

    add_card(s3, Inches(6.8), Inches(4.75), feat_w, feat_h)
    tb_f2 = s3.shapes.add_textbox(Inches(7.0), Inches(4.9), feat_w - Inches(0.4), feat_h - Inches(0.3))
    tff2 = tb_f2.text_frame
    tff2.word_wrap = True
    pf2_t = tff2.paragraphs[0]
    pf2_t.text = "✍️ Аудит черновика и адаптивные ответы"
    pf2_t.font.name = FONT_FAMILY
    pf2_t.font.size = Pt(14)
    pf2_t.font.bold = True
    pf2_t.font.color.rgb = TEXT_TITLE

    pf2_d = tff2.add_paragraph()
    pf2_d.text = (
        "Если вписан черновик ответа, ИИ укажет на его риски. На выбор дается 3–4 готовых стиля "
        "(твердый, дипломатичный, дружелюбный) с обоснованием эффекта каждой фразы."
    )
    pf2_d.font.name = FONT_FAMILY
    pf2_d.font.size = Pt(11)
    pf2_d.font.color.rgb = TEXT_BODY

    # =========================================================================
    # SLIDE 4: ТЕХНИЧЕСКАЯ ЧАСТЬ (БЕЗ РЕКЛАМЫ, ПО ДЕЛУ)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    apply_bg(s4)

    add_badge(s4, "03 • ТЕХНИЧЕСКАЯ ЧАСТЬ", Inches(1.2), Inches(0.8), Inches(3.0), Inches(0.38), ACCENT_INDIGO)

    h4 = s4.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.0))
    tf4 = h4.text_frame
    tf4.word_wrap = True
    p4 = tf4.paragraphs[0]
    p4.text = "Архитектура решения: простота, скорость и безопасность"
    p4.font.name = FONT_FAMILY
    p4.font.size = Pt(28)
    p4.font.bold = True
    p4.font.color.rgb = TEXT_TITLE

    p4_sub = tf4.add_paragraph()
    p4_sub.text = "Разработано как независимый инструмент без необходимости сложной настройки:"
    p4_sub.font.name = FONT_FAMILY
    p4_sub.font.size = Pt(13)
    p4_sub.font.color.rgb = TEXT_MUTED

    tech_blocks = [
        (
            "🖥️ Графический интерфейс (PyQt6)",
            "Легковесный десктопный оверлей",
            "Плавающее фреймлесс-окно всегда под рукой поверх любых приложений. Глобальный перехват Alt+S и интеграция в трей Windows позволяют работать без отвлечения от диалога."
        ),
        (
            "🧠 Нейросетевой анализ по API",
            "Мультимодальная обработка кадров",
            "Скриншоты диалога напрямую передаются в мультимодальную языковую модель по API (Gemini Vision) со строгой JSON-валидацией (Pydantic). Реализовано резервное переключение при лимитах."
        ),
        (
            "🔒 Безопасность и автономность",
            "Без риска бана аккаунтов",
            "Захват идет через системный буфер памяти без записи на диск. Приложение не внедряется в мессенджеры (Telegram, WhatsApp) и скомпилировано в единый EXE-файл без установки Python."
        ),
    ]

    tw = Inches(3.45)
    th = Inches(4.3)
    for i, (title, sub, desc) in enumerate(tech_blocks):
        tx = Inches(1.2) + i * Inches(3.72)
        add_card(s4, tx, Inches(2.55), tw, th)

        bar = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, tx + Inches(0.3), Inches(2.8), Inches(0.4), Inches(0.05))
        bar.fill.solid()
        bar.fill.fore_color.rgb = ACCENT_INDIGO
        bar.line.fill.background()

        tb = s4.shapes.add_textbox(tx + Inches(0.25), Inches(3.05), tw - Inches(0.5), th - Inches(0.7))
        tf = tb.text_frame
        tf.word_wrap = True

        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.name = FONT_FAMILY
        pt.font.size = Pt(14)
        pt.font.bold = True
        pt.font.color.rgb = TEXT_TITLE

        ps = tf.add_paragraph()
        ps.text = sub
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
    # SLIDE 5: ИТОГИ И РЕЗУЛЬТАТЫ
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    apply_bg(s5)

    add_badge(s5, "04 • ИТОГИ И ЦЕННОСТЬ", Inches(1.2), Inches(0.8), Inches(2.8), Inches(0.38), ACCENT_EMERALD)

    h5 = s5.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(10.9), Inches(1.0))
    tf5 = h5.text_frame
    tf5.word_wrap = True
    p5 = tf5.paragraphs[0]
    p5.text = "VibeSense AI: уверенность в каждом сообщении"
    p5.font.name = FONT_FAMILY
    p5.font.size = Pt(28)
    p5.font.bold = True
    p5.font.color.rgb = TEXT_TITLE

    p5_sub = tf5.add_paragraph()
    p5_sub.text = "Сервис превращает невербальный хаос переписок в понятный и управляемый диалог."
    p5_sub.font.name = FONT_FAMILY
    p5_sub.font.size = Pt(13)
    p5_sub.font.color.rgb = TEXT_MUTED

    stats = [
        ("< 2 сек", "Скорость анализа", "От снимка экрана до готовых вариантов ответа под выбранную цель"),
        ("100%", "Совместимость", "Работает в Telegram, Discord, WhatsApp, браузере и любых окнах"),
        ("1 клик", "Автономность", "Собран единый VibeSense.exe — запускается сразу без настроек"),
    ]

    stat_w = Inches(3.45)
    stat_h = Inches(2.2)
    for i, (num, lbl, sub) in enumerate(stats):
        sx = Inches(1.2) + i * Inches(3.72)
        add_card(s5, sx, Inches(2.6), stat_w, stat_h)

        tb = s5.shapes.add_textbox(sx + Inches(0.2), Inches(2.75), stat_w - Inches(0.4), stat_h - Inches(0.3))
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
    callout = add_card(s5, Inches(1.2), Inches(5.15), Inches(10.9), Inches(1.6), CARD_BG_ALT, ACCENT_INDIGO)
    ctb = s5.shapes.add_textbox(Inches(1.5), Inches(5.25), Inches(10.3), Inches(1.4))
    ctf = ctb.text_frame
    ctf.word_wrap = True

    cp1 = ctf.paragraphs[0]
    cp1.text = "🚀 Исходный код и готовый бинарник опубликованы в открытом доступе:"
    cp1.font.name = FONT_FAMILY
    cp1.font.size = Pt(14)
    cp1.font.bold = True
    cp1.font.color.rgb = TEXT_TITLE

    cp2 = ctf.add_paragraph()
    cp2.text = "• Репозиторий проекта:  https://github.com/EgorDushenkov/ELAY"
    cp2.font.name = FONT_FAMILY
    cp2.font.size = Pt(12)
    cp2.font.bold = True
    cp2.font.color.rgb = ACCENT_CYAN

    cp3 = ctf.add_paragraph()
    cp3.text = "• Скачать релиз VibeSense.exe:  https://github.com/EgorDushenkov/ELAY/releases/tag/v1.0.0"
    cp3.font.name = FONT_FAMILY
    cp3.font.size = Pt(12)
    cp3.font.bold = True
    cp3.font.color.rgb = ACCENT_EMERALD

    # Save
    out_v2 = os.path.join(os.path.dirname(__file__), "VibeSense_AI_Presentation_v2.pptx")
    prs.save(out_v2)
    print(f"SUCCESS: Saved {out_v2}")

    out_main = os.path.join(os.path.dirname(__file__), "VibeSense_AI_Presentation.pptx")
    try:
        prs.save(out_main)
        print(f"SUCCESS: Overwritten {out_main}")
    except Exception as e:
        print(f"Notice: Could not overwrite {out_main} (likely open in PowerPoint): {e}")

if __name__ == "__main__":
    create_deck()
