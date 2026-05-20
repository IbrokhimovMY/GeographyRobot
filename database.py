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
            'wrong_capital, timeout_capital FROM users WHERE user_id = ?',
            (user_id,),
        ).fetchone()
    return {
        'correct_country': row[0], 'wrong_country': row[1],
        'correct_capital': row[2], 'wrong_capital': row[3],
        'timeout_capital': row[4],
    }


def get_top_users(limit: int = 10) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            '''SELECT COALESCE(NULLIF(display_name,""), NULLIF(username,""), user_id),
                      correct_country, correct_capital,
                      correct_country + correct_capital AS total
               FROM users ORDER BY total DESC LIMIT ?''',
            (limit,),
        ).fetchall()
    return rows
