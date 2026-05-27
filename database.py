import sqlite3
import logging
from config import DB_PATH, SUPPORTED_LANGS

logger = logging.getLogger(__name__)

_SCORE_COLUMNS: dict[tuple, str] = {
    ('correct', 'country'): 'correct_country',
    ('wrong',   'country'): 'wrong_country',
    ('correct', 'capital'): 'correct_capital',
    ('wrong',   'capital'): 'wrong_capital',
    ('timeout', 'capital'): 'timeout_capital',
}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id         TEXT PRIMARY KEY,
                username        TEXT DEFAULT '',
                display_name    TEXT DEFAULT '',
                language        TEXT DEFAULT 'uz',
                correct_country INTEGER DEFAULT 0,
                wrong_country   INTEGER DEFAULT 0,
                correct_capital INTEGER DEFAULT 0,
                wrong_capital   INTEGER DEFAULT 0,
                timeout_capital INTEGER DEFAULT 0
            )
        ''')
        for col, definition in [
            ('display_name', 'TEXT DEFAULT ""'),
            ('language', "TEXT DEFAULT 'uz'"),
            ('daily_facts', 'INTEGER DEFAULT 0'),
            ('streak', 'INTEGER DEFAULT 0'),
            ('best_streak', 'INTEGER DEFAULT 0'),
            ('difficulty', "TEXT DEFAULT 'normal'"),
            ('continent_filter', "TEXT DEFAULT 'all'"),
        ]:
            try:
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
            except sqlite3.OperationalError:
                pass
    logger.info("Database ready.")


def _ensure_user(conn: sqlite3.Connection, user_id: str, username: str) -> None:
    conn.execute(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username),
    )
    conn.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))


def record_result(user_id: str, username: str, game_type: str, result: str) -> None:
    col = _SCORE_COLUMNS.get((result, game_type))
    if col is None:
        return
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute(f'UPDATE users SET {col} = {col} + 1 WHERE user_id = ?', (user_id,))


def set_display_name(user_id: str, username: str, display_name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute(
            'UPDATE users SET display_name = ? WHERE user_id = ?',
            (display_name, user_id),
        )


def get_display_name(user_id: str, fallback: str = '') -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT display_name, username FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
    if row:
        return row[0] if row[0] else (row[1] if row[1] else fallback)
    return fallback


def get_user_lang(user_id: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT language FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
    if row and row[0] in SUPPORTED_LANGS:
        return row[0]
    return 'uz'


def set_user_lang(user_id: str, username: str, lang: str) -> None:
    if lang not in SUPPORTED_LANGS:
        return
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute(
            'UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id)
        )


def get_stats(user_id: str, username: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        row = conn.execute(
            'SELECT correct_country, wrong_country, correct_capital, '
            'wrong_capital, timeout_capital, streak, best_streak FROM users WHERE user_id = ?',
            (user_id,),
        ).fetchone()
    return {
        'correct_country': row[0], 'wrong_country': row[1],
        'correct_capital': row[2], 'wrong_capital': row[3],
        'timeout_capital': row[4], 'streak': row[5], 'best_streak': row[6],
    }


def increment_streak(user_id: str, username: str) -> tuple[int, bool]:
    """Increment streak, update best if needed. Returns (new_streak, is_new_best)."""
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        row = conn.execute(
            'SELECT streak, best_streak FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
        new_streak = (row[0] if row else 0) + 1
        best = row[1] if row else 0
        new_best = new_streak > best
        conn.execute(
            'UPDATE users SET streak = ?, best_streak = ? WHERE user_id = ?',
            (new_streak, max(new_streak, best), user_id),
        )
    return new_streak, new_best


def reset_streak(user_id: str, username: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute('UPDATE users SET streak = 0 WHERE user_id = ?', (user_id,))


def get_difficulty(user_id: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT difficulty FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
    return row[0] if row and row[0] in ('easy', 'normal', 'hard') else 'normal'


def set_difficulty(user_id: str, username: str, level: str) -> None:
    if level not in ('easy', 'normal', 'hard'):
        return
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute('UPDATE users SET difficulty = ? WHERE user_id = ?', (level, user_id))


def get_continent_filter(user_id: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT continent_filter FROM users WHERE user_id = ?', (user_id,)
        ).fetchone()
    return row[0] if row else 'all'


def set_continent_filter(user_id: str, username: str, continent: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        conn.execute(
            'UPDATE users SET continent_filter = ? WHERE user_id = ?', (continent, user_id)
        )


def toggle_daily_facts(user_id: str, username: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, user_id, username)
        row = conn.execute('SELECT daily_facts FROM users WHERE user_id = ?', (user_id,)).fetchone()
        new_state = 0 if (row and row[0]) else 1
        conn.execute('UPDATE users SET daily_facts = ? WHERE user_id = ?', (new_state, user_id))
    return bool(new_state)


def get_daily_facts_subscribers() -> list:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            'SELECT user_id, language FROM users WHERE daily_facts = 1'
        ).fetchall()


def get_top_users(limit: int = 10) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            '''SELECT COALESCE(NULLIF(display_name,""), NULLIF(username,""), user_id),
                      correct_country + correct_capital AS total_correct,
                      correct_country + wrong_country + correct_capital + wrong_capital + timeout_capital AS total_games
               FROM users
               WHERE correct_country + wrong_country + correct_capital + wrong_capital + timeout_capital > 0
               ORDER BY CAST(correct_country + correct_capital AS REAL) /
                        (correct_country + wrong_country + correct_capital + wrong_capital + timeout_capital) DESC,
                        correct_country + correct_capital DESC
               LIMIT ?''',
            (limit,),
        ).fetchall()
    return rows  # (name, total_correct, total_games)
