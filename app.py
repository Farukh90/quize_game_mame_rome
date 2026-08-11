import os
import time
import base64
import streamlit as st
import streamlit.components.v1 as components
import database as db

# Инициализация базы данных
db.init_db()

# ---------------------------------------------------------
# 1. Настройка страницы и CSS
# ---------------------------------------------------------
font_base64_str = ""
if os.path.exists("font.otf"):
    with open("font.otf", "rb") as f:
        font_base64_str = base64.b64encode(f.read()).decode("utf-8")


def get_font_face_css():
    if not font_base64_str:
        return ""
    return f"""
    @font-face {{
        font-family: 'SimpleproDisplay';
        src: url("data:font/otf;charset=utf-8;base64,{font_base64_str}") format("opentype");
        font-weight: normal;
        font-style: normal;
    }}
    """


st.set_page_config(page_title="SimpleGame", layout="wide", initial_sidebar_state="expanded")

font_css = get_font_face_css()
st.markdown(f"""
    <style>
    {font_css}

    header[data-testid="stHeader"] {{
        background-color: transparent !important;
        z-index: 100 !important;
    }}

    #MainMenu, footer, [data-testid="stAppDeployButton"], .stAppDeployButton {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* Скрываем подпись клавиатурного сокращения (Keyboard_double), сохраняя саму кнопку свертывания */
    [data-testid="stSidebarCollapseButton"] button span,
    [data-testid="stSidebarCollapseButton"] button p,
    button[data-testid="baseButton-headerNoPadding"] span,
    button[data-testid="baseButton-headerNoPadding"] p {{
        display: none !important;
    }}

    .stApp {{
        background-color: #454b4d;
        color: #ffffff;
    }}

    h1, h2, h3, h4, h5, h6, 
    .stMarkdown p, .category-card, .player-card,
    .stButton>button, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
        font-family: 'SimpleproDisplay', sans-serif !important;
    }}

    [data-testid="stHorizontalBlock"] {{
        gap: 0.5rem !important;
        align-items: center;
    }}

    [data-testid="stExpander"] {{
        background-color: #383d3f !important;
        border: 1px solid #ff1428 !important;
        border-radius: 8px !important;
    }}

    [data-testid="stExpander"] summary {{
        font-family: 'SimpleproDisplay', sans-serif !important;
        color: #ffffff !important;
        padding-left: 10px !important;
    }}

    /* Выравнивание категории и кнопок по высоте и убирание внешних отступов */
    .category-card {{
        background-color: #ff1428;
        color: #ffffff;
        font-size: 20px;
        font-weight: bold;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
        padding: 0 10px;
        margin: 0 !important;
    }}

    /* Корректировка контейнеров markdown для идеального выравнивания сетки */
    div[data-testid="stMarkdownContainer"] > p {{
        margin: 0 !important;
    }}

    .stButton {{
        margin: 0 !important;
    }}

    .stButton>button {{
        width: 100% !important;
        height: 70px !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        background-color: #ffffff !important;
        color: #ff1428 !important;
        border: 2px solid #ff1428 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: all 0.15s ease-in-out;
        margin: 0 !important;
    }}

    .stButton>button:hover {{
        background-color: #ff1428 !important;
        color: #ffffff !important;
        transform: scale(1.02);
    }}

    .stButton>button:disabled {{
        visibility: hidden !important;
    }}

    div.stButton > button[key="btn_stop_timer"] {{
        background-color: #ff9800 !important;
        color: #ffffff !important;
        border: 2px solid #e68a00 !important;
        height: 50px !important;
        font-size: 20px !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: #383d3f !important;
        border-right: 1px solid #ff1428;
    }}

    .player-card {{
        background-color: #454b4d;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff1428;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        margin-bottom: 10px;
        text-align: center;
        color: #ffffff;
    }}
    .player-score {{
        font-size: 28px;
        font-weight: bold;
        color: #ff1428;
    }}

    .winner-box {{
        background: linear-gradient(135deg, #ff1428 0%, #b30012 100%);
        border: 4px solid #ffffff;
        border-radius: 16px;
        padding: 40px 20px;
        text-align: center;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        margin-top: 20px;
    }}
    .winner-title {{ font-size: 48px; font-weight: 900; text-transform: uppercase; margin-bottom: 10px; }}
    .winner-name {{ font-size: 40px; color: #fff200; font-weight: bold; margin-bottom: 15px; }}
    .winner-score {{ font-size: 30px; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Инициализация состояния из БД
# ---------------------------------------------------------
if "game_started" not in st.session_state:
    st.session_state.game_started = True

if "mode" not in st.session_state:
    st.session_state.mode = "main"

st.session_state.players = db.load_players()
st.session_state.quiz_data = db.load_quiz_data()

if "current_question" not in st.session_state:
    st.session_state.current_question = None

if "timer_stopped" not in st.session_state:
    st.session_state.timer_stopped = False

# Настройки Блиц-финала
if "blitz_p_index" not in st.session_state:
    st.session_state.blitz_p_index = 0
if "blitz_q_index" not in st.session_state:
    st.session_state.blitz_q_index = 0
if "blitz_scores" not in st.session_state:
    st.session_state.blitz_scores = {}
if "blitz_finished" not in st.session_state:
    st.session_state.blitz_finished = False

st.session_state.timer_default = int(db.get_setting("timer_default", "30"))
st.session_state.timer_blitz = int(db.get_setting("timer_blitz", "15"))
st.session_state.timer_blitz_final = int(db.get_setting("timer_blitz_final", "30"))


def render_header(title_text):
    st.title(title_text)


# ---------------------------------------------------------
# 3. НАСТРОЙКА ИГРЫ (Конструктор)
# ---------------------------------------------------------
if not st.session_state.game_started:
    render_header("⚙️ Настройка «Своей Игры»")

    tab_players, tab_quiz, tab_blitz_setting, tab_settings = st.tabs([
        "👥 Игроки",
        "📚 Вопросы табло",
        "⚡ Блиц-вопросы участников",
        "⏱️ Таймеры"
    ])

    with tab_players:
        st.subheader("Список участников")
        player_names = list(st.session_state.players.keys())
        cols_p = st.columns(3)
        for i, name in enumerate(player_names):
            with cols_p[i % 3]:
                col_name, col_del = st.columns([4, 1])
                col_name.info(f"🙎{name}")
                if len(player_names) > 1:
                    if col_del.button("❌", key=f"del_player_{name}"):
                        db.delete_player(name)
                        st.rerun()

        st.divider()
        col_input, col_add = st.columns([3, 1])
        new_name = col_input.text_input("Имя нового участника:", key="new_player_input")
        if col_add.button("➕ Добавить игрока", use_container_width=True):
            if new_name:
                db.add_player(new_name)
                st.rerun()

    with tab_quiz:
        st.subheader("Текущие темы и вопросы")

        col_cat_in, col_cat_add = st.columns([3, 1])
        new_cat = col_cat_in.text_input("Название новой темы:")
        if col_cat_add.button("➕ Добавить тему", use_container_width=True):
            if new_cat:
                db.add_category(new_cat)
                st.rerun()

        st.divider()

        for cat_name in list(st.session_state.quiz_data.keys()):
            with st.expander(f"📁 Тема: {cat_name}", expanded=False):
                if st.button("Удалить тему", key=f"del_cat_{cat_name}"):
                    db.delete_category(cat_name)
                    st.rerun()

                scores = [100, 200, 300, 400, 500]
                for sc in scores:
                    st.markdown(f"**Вопрос на {sc} баллов**")
                    q_item = st.session_state.quiz_data[cat_name].get(sc, {})
                    curr_q = q_item.get("q", "")
                    curr_a = q_item.get("a", "")
                    curr_blitz = q_item.get("is_blitz", False)

                    c1, c2, c3 = st.columns([3, 3, 1])
                    q_val = c1.text_input(f"Вопрос ({sc})", value=curr_q, key=f"q_{cat_name}_{sc}")
                    a_val = c2.text_input(f"Ответ ({sc})", value=curr_a, key=f"a_{cat_name}_{sc}")
                    blitz_val = c3.checkbox("⚡ БЛИЦ", value=curr_blitz, key=f"blitz_{cat_name}_{sc}")

                    if q_val and (q_val != curr_q or a_val != curr_a or blitz_val != curr_blitz):
                        db.save_question(cat_name, sc, q_val, a_val, blitz_val)

    with tab_blitz_setting:
        st.subheader("Индивидуальные вопросы Блиц-финала")

        player_names = list(st.session_state.players.keys())
        if not player_names:
            st.warning("Сначала добавьте игроков!")
        else:
            p_tabs = st.tabs([f"🙎{p}" for p in player_names])
            for i, p_name in enumerate(player_names):
                with p_tabs[i]:
                    blitz_qs = db.load_blitz_final_questions_for_player(p_name)

                    st.write(f"Вопросы для участника **{p_name}**:")
                    for row in blitz_qs:
                        q_id = row["id"]
                        c_pts, c_q, c_a, c_del = st.columns([1, 4, 4, 1])
                        pts_val = c_pts.number_input("Баллы", value=row["points"], key=f"bq_pts_{q_id}")
                        q_val = c_q.text_input("Вопрос", value=row["question"], key=f"bq_q_{q_id}")
                        a_val = c_a.text_input("Ответ", value=row["answer"], key=f"bq_a_{q_id}")

                        if c_del.button("❌", key=f"del_bq_{q_id}"):
                            db.delete_blitz_final_question(q_id)
                            st.rerun()

                        if (pts_val != row["points"] or q_val != row["question"] or a_val != row["answer"]):
                            db.update_blitz_final_question(q_id, pts_val, q_val, a_val)

                    st.markdown(f"**➕ Добавить вопрос для {p_name}**")
                    cb_pts, cb_q, cb_a, cb_btn = st.columns([1, 4, 4, 1])
                    new_bq_pts = cb_pts.number_input("Баллы", value=100, key=f"new_bq_pts_{p_name}")
                    new_bq_q = cb_q.text_input("Вопрос", key=f"new_bq_q_{p_name}")
                    new_bq_a = cb_a.text_input("Ответ", key=f"new_bq_a_{p_name}")

                    if cb_btn.button("➕", key=f"add_bq_btn_{p_name}"):
                        if new_bq_q and new_bq_a:
                            db.add_blitz_final_question(p_name, new_bq_pts, new_bq_q, new_bq_a)
                            st.rerun()

    with tab_settings:
        st.subheader("Настройки таймеров обратного отсчета")

        c_t1, c_t2, c_t3 = st.columns(3)
        new_t_def = c_t1.number_input("⏱️ Обычный вопрос (сек):", min_value=5, max_value=120,
                                      value=st.session_state.timer_default)
        new_t_blitz = c_t2.number_input("⚡ БЛИЦ в табло (сек):", min_value=3, max_value=60,
                                        value=st.session_state.timer_blitz)
        new_t_blitz_f = c_t3.number_input("⚡ Блиц-финал на игрока (сек):", min_value=5, max_value=300,
                                          value=st.session_state.timer_blitz_final)

        if new_t_def != st.session_state.timer_default:
            db.set_setting("timer_default", new_t_def)
        if new_t_blitz != st.session_state.timer_blitz:
            db.set_setting("timer_blitz", new_t_blitz)
        if new_t_blitz_f != st.session_state.timer_blitz_final:
            db.set_setting("timer_blitz_final", new_t_blitz_f)

    st.divider()
    if st.button("🚀 ЗАПУСТИТЬ ИГРУ", type="primary", use_container_width=True):
        if not st.session_state.quiz_data:
            st.error("Добавьте хотя бы одну тему!")
        else:
            st.session_state.game_started = True
            st.rerun()

# ---------------------------------------------------------
# 4. ИГРОВОЙ ЭКРАН
# ---------------------------------------------------------
else:
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)

        st.header("🙎 Игроки")
        for player, score in st.session_state.players.items():
            st.markdown(f"""
                <div class="player-card">
                    <div style="font-size: 14px; color: #d0d7de;">{player}</div>
                    <div class="player-score">{score} б.</div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        if st.session_state.mode == "main":
            if st.button("⚡ Запустить Блиц-финал", use_container_width=True):
                st.session_state.mode = "blitz_final"
                st.session_state.blitz_p_index = 0
                st.session_state.blitz_q_index = 0
                st.session_state.blitz_started = False  # <-- Добавлено здесь
                st.session_state.blitz_scores = {p: 0 for p in st.session_state.players}
                st.session_state.blitz_finished = False
                if "blitz_start_time" in st.session_state:
                    del st.session_state.blitz_start_time
                st.rerun()
        else:
            if st.button("⬅ Вернуться к Табло", use_container_width=True):
                st.session_state.mode = "main"
                st.rerun()

        if st.button("⚙️ Настройки игры", use_container_width=True):
            st.session_state.game_started = False
            st.rerun()

        if st.button("🔄 Сбросить счет и вопросы", use_container_width=True):
            st.session_state.current_question = None
            st.session_state.timer_stopped = False
            st.session_state.mode = "main"
            st.session_state.blitz_finished = False
            db.reset_all_scores()
            db.reset_all_questions()
            st.rerun()

    # ---------------------------------------------------------
    # РЕЖИМ БЛИЦ-ФИНАЛА
    # ---------------------------------------------------------
    if st.session_state.mode == "blitz_final":
        render_header("⚡ РЕЖИМ «БЛИЦ-ФИНАЛ»")

        players_list = list(st.session_state.players.keys())

        if st.session_state.blitz_finished or st.session_state.blitz_p_index >= len(players_list):
            st.session_state.blitz_finished = True
            st.balloons()

            total_scores = {}
            for p in players_list:
                main_score = st.session_state.players.get(p, 0)
                blitz_score = st.session_state.blitz_scores.get(p, 0)
                total_scores[p] = main_score + blitz_score

            winner = max(total_scores, key=total_scores.get)
            winner_score = total_scores[winner]

            st.markdown(f"""
                <div class="winner-box">
                    <div class="winner-title">🏆 ПОБЕДИТЕЛЬ ИГРЫ 🏆</div>
                    <div class="winner-name">{winner}</div>
                    <div class="winner-score">Суммарный результат: <b>{winner_score} баллов</b></div>
                </div>
            """, unsafe_allow_html=True)

            st.subheader("📊 Итоговая таблица результатов:")
            for p in players_list:
                m_sc = st.session_state.players.get(p, 0)
                b_sc = st.session_state.blitz_scores.get(p, 0)
                tot = m_sc + b_sc
                st.write(f"• **{p}**: Табло ({m_sc}) + Блиц ({b_sc}) = **{tot} баллов**")

        else:
            current_player = players_list[st.session_state.blitz_p_index]
            blitz_questions = db.load_blitz_final_questions_for_player(current_player)

            st.subheader(f"Ход игрока: 🙎 **{current_player}**")
            st.markdown(f"Набрано очков в блице: **{st.session_state.blitz_scores.get(current_player, 0)}**")

            # Проверяем, нажал ли игрок кнопку старта хода
            if not st.session_state.get("blitz_started", False):
                st.info(
                    f"Игрок **{current_player}**, приготовьтесь! Нажмите кнопку ниже, чтобы запустить таймер и открыть первый вопрос.")
                if st.button("🚀 ПОЕХАЛИ!", type="primary", use_container_width=True):
                    st.session_state.blitz_started = True
                    st.session_state.blitz_start_time = time.time()
                    st.session_state.blitz_current_p = current_player
                    st.rerun()

            elif not blitz_questions:
                st.warning(f"Для участника {current_player} нет вопросов в Блиц-финале! Добавьте их в настройках.")
                if st.button("▶ Пропустить игрока", use_container_width=True):
                    st.session_state.blitz_p_index += 1
                    st.session_state.blitz_q_index = 0
                    st.session_state.blitz_started = False
                    if "blitz_start_time" in st.session_state:
                        del st.session_state.blitz_start_time
                    st.rerun()

            else:
                q_idx = st.session_state.blitz_q_index
                time_limit = st.session_state.timer_blitz_final

                elapsed = int(time.time() - st.session_state.get("blitz_start_time", time.time()))
                time_left = max(0, time_limit - elapsed)

                if time_left == 0 or q_idx >= len(blitz_questions):
                    if time_left == 0:
                        st.error("⏳ ВРЕМЯ ИГРОКА ИСТЕКЛО!")
                    else:
                        st.success("🎉 Игрок ответил на все свои вопросы!")

                    if st.button("▶ Перейти к следующему игроку", type="primary", use_container_width=True):
                        st.session_state.blitz_p_index += 1
                        st.session_state.blitz_q_index = 0
                        st.session_state.blitz_started = False
                        if "blitz_start_time" in st.session_state:
                            del st.session_state.blitz_start_time
                        st.rerun()

                else:
                    current_q = blitz_questions[q_idx]

                    blitz_card_html = f"""
                    <style>
                        {font_css}
                        * {{ font-family: 'SimpleproDisplay', sans-serif !important; margin: 0; padding: 0; box-sizing: border-box; }}

                        .timer-box {{
                            background-color: #383d3f; border: 2px solid #ff1428; border-radius: 10px;
                            padding: 12px; text-align: center; margin-bottom: 15px;
                        }}
                        .timer-text {{ font-size: 26px; font-weight: bold; color: #ffffff; }}
                        .timer-text.danger {{ color: #ff1428; }}

                        .flip-card {{ background-color: transparent; width: 100%; height: 210px; perspective: 1000px; }}
                        .flip-card-inner {{
                            position: relative; width: 100%; height: 100%; text-align: center;
                            transition: transform 0.4s ease-out; transform-style: preserve-3d;
                        }}
                        .card-face {{
                            position: absolute; width: 100%; height: 100%;
                            -webkit-backface-visibility: hidden; backface-visibility: hidden;
                            border-radius: 12px; box-shadow: 0 6px 12px rgba(0,0,0,0.4);
                            display: flex; flex-direction: column; justify-content: center;
                            align-items: center; padding: 15px;
                        }}
                        .face-question {{ background-color: #383d3f; color: #ffffff; border: 3px solid #ff1428; }}
                        .face-answer {{ background-color: rgb(46, 134, 86); color: #ffffff; border: 3px solid #1f5c3b; transform: rotateY(180deg); }}
                        .flip-card-inner.state-answer {{ transform: rotateY(180deg) !important; }}

                        .q-num {{ font-size: 13px; color: #ff1428; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }}
                        .q-text {{ font-size: 24px; font-weight: 600; line-height: 1.2; }}
                        .a-text {{ font-size: 28px; font-weight: 800; }}

                        .show-btn {{
                            margin-top: 12px; background-color: #ff1428; color: #ffffff; border: none;
                            padding: 8px 18px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;
                        }}
                    </style>

                    <div class="timer-box">
                        <div id="timerDisplay" class="timer-text">⏱️ ОСТАЛОСЬ ВРЕМЕНИ: {time_left} сек</div>
                    </div>

                    <div class="flip-card">
                        <div class="flip-card-inner" id="bCardInner">
                            <div class="card-face face-question">
                                <div class="q-num">Вопрос {q_idx + 1} из {len(blitz_questions)} (+{current_q['points']} б.)</div>
                                <div class="q-text">{current_q['question']}</div>
                                <button class="show-btn" onclick="document.getElementById('bCardInner').classList.add('state-answer')">👁 Показать ответ</button>
                            </div>
                            <div class="card-face face-answer">
                                <div style="font-size: 13px; color: #d4edda; font-weight: bold;">ОТВЕТ:</div>
                                <div class="a-text">✅ {current_q['answer']}</div>
                            </div>
                        </div>
                    </div>

                    <script>
                        let timeLeft = {time_left};
                        const timerEl = document.getElementById('timerDisplay');

                        const countdown = setInterval(() => {{
                            timeLeft--;
                            if (timeLeft <= 0) {{
                                clearInterval(countdown);
                                timerEl.innerText = "⏳ ВРЕМЯ ИСТЕКЛО!";
                                timerEl.classList.add('danger');
                            }} else {{
                                timerEl.innerText = `⏱️ ОСТАЛОСЬ ВРЕМЕНИ: ${{timeLeft}} сек`;
                                if (timeLeft <= 5) {{
                                    timerEl.classList.add('danger');
                                }}
                            }}
                        }}, 1000);
                    </script>
                    """

                    components.html(blitz_card_html, height=310)

                    col1, col2, col3 = st.columns(3)
                    if col1.button("✅ Верно", key=f"blitz_win_{q_idx}", use_container_width=True):
                        st.session_state.blitz_scores[current_player] += current_q['points']
                        st.session_state.blitz_q_index += 1
                        st.rerun()

                    if col2.button("❌ Мимо / Пропуск", key=f"blitz_lose_{q_idx}", use_container_width=True):
                        st.session_state.blitz_q_index += 1
                        st.rerun()

                    if col3.button("⏹ Досрочно завершить", key=f"blitz_stop_{q_idx}", use_container_width=True):
                        st.session_state.blitz_q_index = len(blitz_questions)
                        st.rerun()

    # ---------------------------------------------------------
    # РЕЖИМ ОСНОВНОЙ ИГРЫ (ТАБЛО)
    # ---------------------------------------------------------
    else:
        render_header("SimpleGame")

        if st.session_state.current_question:
            q_info = st.session_state.current_question
            cat, points = q_info["cat"], q_info["points"]
            data = st.session_state.quiz_data[cat][points]

            is_blitz = data.get("is_blitz", False)
            time_limit = st.session_state.timer_blitz if is_blitz else st.session_state.timer_default
            badge_title = "⚡ БЛИЦ-ВОПРОС" if is_blitz else f"{cat} — {points} баллов"

            is_already_stopped_js = "true" if st.session_state.timer_stopped else "false"

            flip_card_html = f"""
            <style>
                {font_css}
                * {{ font-family: 'SimpleproDisplay', 'Segoe UI', sans-serif !important; }}
                .flip-card {{ background-color: transparent; width: 100%; height: 280px; perspective: 1000px; }}
                .flip-card-inner {{
                    position: relative; width: 100%; height: 100%; text-align: center;
                    transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    transform-style: preserve-3d; transform: rotateY(0deg);
                }}
                .card-face {{
                    position: absolute; width: 100%; height: 100%;
                    -webkit-backface-visibility: hidden; backface-visibility: hidden;
                    border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.4);
                    display: flex; flex-direction: column; justify-content: center;
                    align-items: center; padding: 20px; box-sizing: border-box;
                }}
                .face-question {{ background-color: #454b4d; color: #ffffff; border: 4px solid #ff1428; transform: rotateY(0deg); }}
                .face-answer {{ background-color: rgb(46, 134, 86); color: #ffffff; border: 4px solid #1f5c3b; transform: rotateY(180deg); }}
                .flip-card-inner.state-answer {{ transform: rotateY(180deg) !important; }}
                .question-text {{ font-size: 24px; font-weight: 600; margin-bottom: 15px; }}
                .answer-text {{ font-size: 32px; font-weight: 800; color: #ffffff; margin-top: 10px; }}
                .timer-badge {{
                    font-size: 18px; font-weight: bold; color: #ffffff; background: #ff1428;
                    padding: 6px 20px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }}
                .show-answer-btn {{
                    margin-top: 15px; background-color: #ff1428; color: #ffffff; border: none;
                    padding: 10px 24px; font-size: 18px; font-weight: bold; border-radius: 8px;
                    cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.15s, background-color 0.15s;
                }}
                .show-answer-btn:hover {{ background-color: #d80f20; transform: scale(1.05); }}
            </style>

            <div class="flip-card">
                <div class="flip-card-inner" id="cardInner">
                    <div class="card-face face-question">
                        <div style="font-size: 16px; color: #ff1428; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">{badge_title}</div>
                        <div class="question-text">{data['q']}</div>
                        <div class="timer-badge" id="timer">⏱️ Осталось: {time_limit} сек</div>
                        <button class="show-answer-btn" id="showAnswerBtn" style="display: none;" onclick="showAnswer()">👁 Показать ответ</button>
                    </div>
                    <div class="card-face face-answer">
                        <div style="font-size: 16px; color: #d4edda; font-weight: bold; text-transform: uppercase;">Правильный ответ:</div>
                        <div class="answer-text">✅ {data['a']}</div>
                    </div>
                </div>
            </div>

            <script>
                const cardInner = document.getElementById('cardInner');
                const timerEl = document.getElementById('timer');
                const showBtn = document.getElementById('showAnswerBtn');

                let timeLeft = {time_limit};
                let isStopped = {is_already_stopped_js};

                function stopTimerAndShowBtn() {{
                    if (typeof interval !== 'undefined') clearInterval(interval);
                    timerEl.style.display = 'none';
                    showBtn.style.display = 'inline-block';
                }}

                if (isStopped) {{
                    stopTimerAndShowBtn();
                }} else {{
                    var interval = setInterval(() => {{
                        timeLeft--;
                        if (timeLeft <= 0) {{
                            stopTimerAndShowBtn();
                        }} else {{
                            timerEl.innerText = "⏱️ Осталось: " + timeLeft + " сек";
                        }}
                    }}, 1000);
                }}

                function showAnswer() {{
                    stopTimerAndShowBtn();
                    cardInner.classList.add('state-answer');
                }}
            </script>
            """

            components.html(flip_card_html, height=290)

            if not st.session_state.timer_stopped:
                if st.button("⏱️ Завершить таймер досрочно", key="btn_stop_timer", use_container_width=True):
                    st.session_state.timer_stopped = True
                    st.rerun()

            st.markdown("### Начисление баллов:")
            cols = st.columns(len(st.session_state.players))

            for idx, (player, _) in enumerate(st.session_state.players.items()):
                with cols[idx]:
                    st.write(f"**{player}**")

                    if st.button(f"✅ +{points}", key=f"win_{player}"):
                        db.update_player_score(player, points)
                        db.mark_question_as_answered(cat, points)
                        st.session_state.current_question = None
                        st.session_state.timer_stopped = False
                        st.rerun()

                    if st.button(f"❌ -{points}", key=f"lose_{player}"):
                        db.update_player_score(player, -points)
                        db.mark_question_as_answered(cat, points)
                        st.session_state.current_question = None
                        st.session_state.timer_stopped = False
                        st.rerun()

            if st.button("⬅ Назад к табло (никто не ответил)", type="secondary"):
                db.mark_question_as_answered(cat, points)
                st.session_state.current_question = None
                st.session_state.timer_stopped = False
                st.rerun()

        else:
            scores = [100, 200, 300, 400, 500]

            for cat_name, cat_questions in st.session_state.quiz_data.items():
                cols = st.columns([1.8, 1, 1, 1, 1, 1], gap="small")

                with cols[0]:
                    st.markdown(f'<div class="category-card">{cat_name}</div>', unsafe_allow_html=True)

                for idx, score in enumerate(scores):
                    with cols[idx + 1]:
                        q_data = cat_questions.get(score, {})
                        has_question = bool(q_data.get("q"))
                        is_answered = bool(q_data.get("is_answered", 0))
                        is_blitz = q_data.get("is_blitz", False)

                        btn_label = f"⚡ {score}" if is_blitz else f"{score}"

                        if has_question:
                            if st.button(
                                    btn_label,
                                    key=f"btn_{cat_name}_{score}",
                                    disabled=is_answered,
                                    use_container_width=True
                            ):
                                st.session_state.current_question = {"cat": cat_name, "points": score}
                                st.session_state.timer_stopped = False
                                st.rerun()