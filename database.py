import os
import logging
from contextlib import contextmanager

from config import DB_PATH, SUPPORTED_LANGS

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', '')
# Railway (and Heroku) gives postgres:// but psycopg2 requires postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2
else:
    import sqlite3

_SCORE_COLUMNS: dict[tuple, str] = {
    ('correct', 'country'): 'correct_country',
    ('wrong',   'country'): 'wrong_country',
    ('correct', 'capital'): 'correct_capital',
    ('wrong',   'capital'): 'wrong_capital',
    ('timeout', 'capital'): 'timeout_capital',
}


def _q(sql: str) -> str:
    """Replace ? placeholders with %s for PostgreSQL."""
    return sql.replace('?', '%s') if USE_PG else sql


@contextmanager
def _get_conn():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _exec(conn, sql: str, params=()):
    """Execute SQL and return a cursor (works for both sqlite3 and psycopg2)."""
    sql = _q(sql)
    if USE_PG:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur
    else:
        return conn.execute(sql, params)


def init_db() -> None:
    with _get_conn() as conn:
        _exec(conn, '''
            CREATE TABLE IF NOT EXISTS users (
                user_id          TEXT PRIMARY KEY,
                username         TEXT DEFAULT '',
                display_name     TEXT DEFAULT '',
                language         TEXT DEFAULT 'uz',
                correct_country  INTEGER DEFAULT 0,
                wrong_country    INTEGER DEFAULT 0,
                correct_capital  INTEGER DEFAULT 0,
                wrong_capital    INTEGER DEFAULT 0,
                timeout_capital  INTEGER DEFAULT 0,
                daily_facts      INTEGER DEFAULT 0,
                streak           INTEGER DEFAULT 0,
                best_streak      INTEGER DEFAULT 0,
                difficulty       TEXT DEFAULT 'normal',
                continent_filter TEXT DEFAULT 'all'
            )
        ''')
        if not USE_PG:
            # Add any missing columns to existing SQLite databases
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
    logger.info("Database ready (%s).", "PostgreSQL" if USE_PG else "SQLite")


def _ensure_user(conn, user_id: str, username: str) -> None:
    if USE_PG:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING',
            (user_id, username),
        )
        cur.execute('UPDATE users SET username = %s WHERE user_id = %s', (username, user_id))
    else:
        conn.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.execute('UPDATE users SET username = ? WHERE user_id = ?', (username, user_id))


def record_result(user_id: str, username: str, game_type: str, result: str) -> None:
    col = _SCORE_COLUMNS.get((result, game_type))
    if col is None:
        return
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        _exec(conn, f'UPDATE users SET {col} = {col} + 1 WHERE user_id = ?', (user_id,))


def set_display_name(user_id: str, username: str, display_name: str) -> None:
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        _exec(conn, 'UPDATE users SET display_name = ? WHERE user_id = ?', (display_name, user_id))


def get_display_name(user_id: str, fallback: str = '') -> str:
    with _get_conn() as conn:
        row = _exec(conn, 'SELECT display_name, username FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if row:
        return row[0] if row[0] else (row[1] if row[1] else fallback)
    return fallback


def get_user_lang(user_id: str) -> str:
    with _get_conn() as conn:
        row = _exec(conn, 'SELECT language FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if row and row[0] in SUPPORTED_LANGS:
        return row[0]
    return 'uz'


def set_user_lang(user_id: str, username: str, lang: str) -> None:
    if lang not in SUPPORTED_LANGS:
        return
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        _exec(conn, 'UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))


def get_stats(user_id: str, username: str) -> dict:
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        row = _exec(conn,
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
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        row = _exec(conn, 'SELECT streak, best_streak FROM users WHERE user_id = ?', (user_id,)).fetchone()
        new_streak = (row[0] if row else 0) + 1
        best = row[1] if row else 0
        new_best = new_streak > best
        _exec(conn,
            'UPDATE users SET streak = ?, best_streak = ? WHERE user_id = ?',
            (new_streak, max(new_streak, best), user_id),
        )
    return new_streak, new_best


def reset_streak(user_id: str, username: str) -> None:
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        _exec(conn, 'UPDATE users SET streak = 0 WHERE user_id = ?', (user_id,))


def get_difficulty(user_id: str) -> str:
    with _get_conn() as conn:
        row = _exec(conn, 'SELECT difficulty FROM users WHERE user_id = ?', (user_id,)).fetchone()
    return row[0] if row and row[0] in ('easy', 'normal', 'hard') else 'normal'


def set_difficulty(user_id: str, username: str, level: str) -> None:
    if level not in ('easy', 'normal', 'hard'):
        return
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        _exec(conn, 'UPDATE users SET difficulty = ? WHERE user_id = ?', (level, user_id))


def get_continent_filter(user_id: str) -> str:
    with _get_conn() as conn:
        row = _exec(conn, 'SELECT continent_filter FROM users WHERE user_id = ?', (user_id,)).fetchone()
    return row[0] if row else 'all'


def set_continent_filter(user_id: str, username: str, continent: str) -> None:
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        _exec(conn, 'UPDATE users SET continent_filter = ? WHERE user_id = ?', (continent, user_id))


def toggle_daily_facts(user_id: str, username: str) -> bool:
    with _get_conn() as conn:
        _ensure_user(conn, user_id, username)
        row = _exec(conn, 'SELECT daily_facts FROM users WHERE user_id = ?', (user_id,)).fetchone()
        new_state = 0 if (row and row[0]) else 1
        _exec(conn, 'UPDATE users SET daily_facts = ? WHERE user_id = ?', (new_state, user_id))
    return bool(new_state)


def get_daily_facts_subscribers() -> list:
    with _get_conn() as conn:
        return _exec(conn, 'SELECT user_id, language FROM users WHERE daily_facts = 1').fetchall()


def get_top_users(limit: int = 10) -> list:
    with _get_conn() as conn:
        return _exec(conn,
            '''SELECT COALESCE(NULLIF(display_name, ''), NULLIF(username, ''), user_id),
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
