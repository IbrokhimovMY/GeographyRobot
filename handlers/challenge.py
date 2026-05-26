"""Daily challenge: deterministic country per day, same for all users."""
import html
import logging
import random
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from data import COUNTRIES, COUNTRY_CONTINENTS
from database import get_user_lang, get_display_name, record_result
from keyboards import default_kb, guess_kb
from state import active_country_games, active_capital_games, cancel_capital_job, cancel_country_job, cancel_flag_job, new_hint_data
from handlers.flag import active_flag_games
from translations import t, get_hint, get_country_name
from data import COUNTRY_HINTS_UZ

logger = logging.getLogger(__name__)

_challenge_state: dict = {}  # {'date': str, 'country': str, 'solvers': set()}


def _today_country() -> str:
    today = str(date.today())
    if _challenge_state.get('date') != today:
        rng = random.Random(date.today().toordinal())
        _challenge_state['date'] = today
        _challenge_state['country'] = rng.choice(COUNTRIES)
        _challenge_state['solvers'] = set()
    return _challenge_state['country']


def mark_solved(user_id: str) -> None:
    _today_country()
    _challenge_state['solvers'].add(user_id)


def already_solved(user_id: str) -> bool:
    _today_country()
    return user_id in _challenge_state['solvers']


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


def _uname(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)


def _chat_id(update: Update) -> str:
    return str(update.effective_chat.id)


def _is_group(update: Update) -> bool:
    return update.effective_chat.type in ('group', 'supergroup')


def _lang(update: Update) -> str:
    return get_user_lang(_uid(update))


async def get_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = _uid(update)
    chat_id = _chat_id(update)
    lang = _lang(update)
    country_uz = _today_country()

    if already_solved(user_id):
        country_display = html.escape(get_country_name(country_uz, lang))
        await update.message.reply_text(
            t(lang, 'challenge_done', country=country_display),
            parse_mode='HTML', reply_markup=default_kb(lang),
        )
        return

    cancel_capital_job(chat_id)
    cancel_country_job(chat_id)
    cancel_flag_job(chat_id)
    active_capital_games.pop(chat_id, None)
    active_flag_games.pop(chat_id, None)
    active_country_games[chat_id] = {
        'country': country_uz, 'challenge': True,
        'attempts': 0, 'hint_data': new_hint_data(), 'job': None,
    }

    hint_text = get_hint(country_uz, lang, COUNTRY_HINTS_UZ)
    msg = t(lang, 'challenge_question', hint=hint_text)
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=guess_kb(lang))
    logger.info("Challenge: chat=%s user=%s → %s", chat_id, user_id, country_uz)
