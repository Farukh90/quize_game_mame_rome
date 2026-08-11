import sqlite3

DB_NAME = "quiz_game.db"


def get_connection():
    """Создает подключение к базе данных SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация таблиц базы данных и миграция."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Таблица категорий/тем
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Таблица вопросов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                is_blitz INTEGER DEFAULT 0,
                is_answered INTEGER DEFAULT 0,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
                UNIQUE(category_id, points)
            )
        """)

        # Таблица игроков
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                score INTEGER DEFAULT 0
            )
        """)

        # Таблица вопросов для Блиц-финала
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blitz_final_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL DEFAULT '',
                points INTEGER NOT NULL DEFAULT 100,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                FOREIGN KEY (player_name) REFERENCES players (name) ON DELETE CASCADE
            )
        """)

        # МИГРАЦИЯ: проверка и добавление колонки player_name, если БД уже существовала
        cursor.execute("PRAGMA table_info(blitz_final_questions)")
        columns = [column[1] for column in cursor.fetchall()]
        if "player_name" not in columns:
            cursor.execute("ALTER TABLE blitz_final_questions ADD COLUMN player_name TEXT NOT NULL DEFAULT ''")

        # Таблица настроек
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()

    _seed_initial_data()


def _seed_initial_data():
    """Первоначальное заполнение дефолтными данными."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            default_quiz = {
                "Наука": {
                    100: {"q": "Какая планета прозвана «Красной планетой»?", "a": "Марс", "is_blitz": False},
                    200: {"q": "Сколько хромосом у человека в норме?", "a": "46 (23 пары)", "is_blitz": False},
                    300: {"q": "БЛИЦ: Назовите элемент с атомным номером 1 за 15 секунд!", "a": "Водород", "is_blitz": True},
                    400: {"q": "Чему равна скорость света в вакууме?", "a": "300 000 км/с", "is_blitz": False},
                    500: {"q": "Как называется процесс деления клеток?", "a": "Митоз", "is_blitz": False}
                },
                "История": {
                    100: {"q": "В каком году произошла Октябрьская революция?", "a": "1917", "is_blitz": False},
                    200: {"q": "Кто был первым императором Всероссийским?", "a": "Пётр I", "is_blitz": False},
                    300: {"q": "В каком веке было Крещение Руси?", "a": "X век (988 год)", "is_blitz": False},
                    400: {"q": "Как назывался план нападения Германии на СССР?", "a": "Барбаросса", "is_blitz": False},
                    500: {"q": "БЛИЦ: В каком году пала Западная Римская империя?", "a": "476 год", "is_blitz": True}
                }
            }

            for cat_name, questions in default_quiz.items():
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
                cat_id = cursor.lastrowid
                for points, data in questions.items():
                    cursor.execute("""
                        INSERT INTO questions (category_id, points, question, answer, is_blitz, is_answered)
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (cat_id, points, data["q"], data["a"], 1 if data["is_blitz"] else 0))

        cursor.execute("SELECT COUNT(*) FROM players")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO players (name, score) VALUES ('Игрок 1', 0)")
            cursor.execute("INSERT INTO players (name, score) VALUES ('Игрок 2', 0)")

        # Заполнение Блиц-вопросов для дефолтных игроков
        cursor.execute("SELECT COUNT(*) FROM blitz_final_questions")
        if cursor.fetchone()[0] == 0:
            default_blitz_p1 = [
                ("Игрок 1", 100, "Самое глубокое озеро в мире?", "Байкал"),
                ("Игрок 1", 100, "Столица Франции?", "Париж"),
                ("Игрок 1", 100, "Сколько градусов в прямом угле?", "90")
            ]
            default_blitz_p2 = [
                ("Игрок 2", 100, "Какая столица у Японии?", "Токио"),
                ("Игрок 2", 100, "Автор романа «Война и мир»?", "Лев Толстой"),
                ("Игрок 2", 100, "Сколько планет в Солнечной системе?", "8")
            ]
            cursor.executemany("INSERT INTO blitz_final_questions (player_name, points, question, answer) VALUES (?, ?, ?, ?)", default_blitz_p1 + default_blitz_p2)

        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('timer_default', '30')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('timer_blitz', '15')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('timer_blitz_final', '30')")

        conn.commit()


# ==========================================
# ВОПРОСЫ И КАТЕГОРИИ
# ==========================================

def load_quiz_data():
    quiz_data = {}
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()

        for cat in categories:
            cat_id, cat_name = cat["id"], cat["name"]
            quiz_data[cat_name] = {}

            cursor.execute("""
                SELECT points, question, answer, is_blitz, is_answered 
                FROM questions 
                WHERE category_id = ?
            """, (cat_id,))

            for row in cursor.fetchall():
                quiz_data[cat_name][row["points"]] = {
                    "q": row["question"],
                    "a": row["answer"],
                    "is_blitz": bool(row["is_blitz"]),
                    "is_answered": row["is_answered"]
                }
    return quiz_data


def mark_question_as_answered(cat_name, points):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE questions 
            SET is_answered = 1 
            WHERE category_id = (SELECT id FROM categories WHERE name = ?) AND points = ?
        """, (cat_name, points))
        conn.commit()


def reset_all_questions():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET is_answered = 0")
        conn.commit()


def add_category(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def delete_category(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
        conn.commit()


def save_question(cat_name, points, question, answer, is_blitz):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        cat_row = cursor.fetchone()
        if cat_row:
            cat_id = cat_row["id"]
            cursor.execute("""
                INSERT INTO questions (category_id, points, question, answer, is_blitz)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(category_id, points) DO UPDATE SET
                    question = excluded.question,
                    answer = excluded.answer,
                    is_blitz = excluded.is_blitz
            """, (cat_id, points, question, answer, 1 if is_blitz else 0))
            conn.commit()


# ==========================================
# БЛИЦ-ФИНАЛ (ПО ИГРОКАМ)
# ==========================================

def load_blitz_final_questions_for_player(player_name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, points, question, answer FROM blitz_final_questions WHERE player_name = ? ORDER BY id ASC", (player_name,))
        return [dict(row) for row in cursor.fetchall()]


def add_blitz_final_question(player_name, points, question, answer):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO blitz_final_questions (player_name, points, question, answer) VALUES (?, ?, ?, ?)", (player_name, points, question, answer))
        conn.commit()


def update_blitz_final_question(q_id, points, question, answer):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE blitz_final_questions SET points = ?, question = ?, answer = ? WHERE id = ?", (points, question, answer, q_id))
        conn.commit()


def delete_blitz_final_question(q_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM blitz_final_questions WHERE id = ?", (q_id,))
        conn.commit()


# ==========================================
# ИГРОКИ
# ==========================================

def load_players():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, score FROM players")
        rows = cursor.fetchall()
        return {row["name"]: row["score"] for row in rows}


def add_player(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO players (name, score) VALUES (?, 0)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def delete_player(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM blitz_final_questions WHERE player_name = ?", (name,))
        cursor.execute("DELETE FROM players WHERE name = ?", (name,))
        conn.commit()


def update_player_score(name, delta):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET score = score + ? WHERE name = ?", (delta, name))
        conn.commit()


def reset_all_scores():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET score = 0")
        conn.commit()


# ==========================================
# НАСТРОЙКИ
# ==========================================

def get_setting(key, default_value):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default_value


def set_setting(key, value):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()