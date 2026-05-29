"""Currency game: show a currency name+code, user guesses the country."""
import logging
import random

from telegram import Update
from telegram.ext import ContextTypes

from data import COUNTRIES, COUNTRY_CURRENCIES, COUNTRY_CONTINENTS
from database import get_user_lang, get_difficulty, get_continent_filter
from keyboards import default_kb, guess_kb
from state import (
    active_country_games, active_capital_games, active_flag_games, active_currency_games,
    cancel_capital_job, cancel_country_job, cancel_flag_job, cancel_currency_job, new_hint_data,
)
from translations import t, get_country_name

logger = logging.getLogger(__name__)

_CURRENCY_TIME = {'easy': 120, 'normal': 90, 'hard': 60}


def _uid(u: Update) -> str:  return str(u.effective_user.id)
def _uname(u: Update) -> str:
    us = u.effective_user
    return us.username or us.first_name or str(us.id)
def _chat_id(u: Update) -> str: return str(u.effective_chat.id)
def _lang(u: Update) -> str:    return get_user_lang(_uid(u))


async def get_currency_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    user_id = _uid(update)
    lang = _lang(update)
    difficulty = get_difficulty(user_id)
    timeout_sec = _CURRENCY_TIME.get(difficulty, 90)

    cancel_capital_job(chat_id)
    cancel_country_job(chat_id)
    cancel_flag_job(chat_id)
    active_country_games.pop(chat_id, None)
    active_capital_games.pop(chat_id, None)
    active_flag_games.pop(chat_id, None)
    active_currency_games.pop(chat_id, None)

    continent = get_continent_filter(user_id)
    pool = [c for c in COUNTRIES
            if (continent == 'all' or COUNTRY_CONTINENTS.get(c) == continent)
            and c in COUNTRY_CURRENCIES and COUNTRY_CURRENCIES[c][0]]

    if not pool:
        await update.message.reply_text(t(lang, 'no_countries'), reply_markup=default_kb(lang))
        return

    country_uz = random.choice(pool)
    cur_name, cur_code = COUNTRY_CURRENCIES[country_uz]

    job = context.job_queue.run_once(
        callback=_timeout_currency,
        when=timeout_sec,
        data={'chat_id': chat_id, 'country': country_uz, 'lang': lang},
        name=f"currency_timeout_{chat_id}",
    )
    active_currency_games[chat_id] = {
        'country': country_uz, 'attempts': 0,
        'hint_data': new_hint_data(), 'job': job,
    }

    msg = t(lang, 'currency_question', currency=cur_name, code=cur_code)
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=guess_kb(lang))
    logger.info("Currency game: chat=%s → %s [%s]", chat_id, country_uz, difficulty)


async def _timeout_currency(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    country_uz = data['country']
    lang = data.get('lang', 'uz')
    if chat_id in active_currency_games and active_currency_games[chat_id]['country'] == country_uz:
        del active_currency_games[chat_id]
        country_display = get_country_name(country_uz, lang)
        cur_name, cur_code = COUNTRY_CURRENCIES[country_uz]
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=t(lang, 'timeout_currency', country=country_display,
                   currency=cur_name, code=cur_code),
            parse_mode='HTML',
            reply_markup=default_kb(lang),
        )
