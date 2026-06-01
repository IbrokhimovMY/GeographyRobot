"""Flag game: show a flag emoji, user guesses the country."""
import logging
import random
from collections import defaultdict

from telegram import Update
from telegram.ext import ContextTypes

from data import COUNTRIES, COUNTRY_FLAGS, COUNTRY_CONTINENTS
from database import get_user_lang, get_difficulty, get_continent_filter, record_result, reset_streak
from keyboards import default_kb, guess_kb
from state import (
    active_country_games, active_capital_games, active_flag_games,
    used_country_countries, cancel_capital_job, cancel_country_job, cancel_flag_job,
    new_hint_data,
)
from translations import t, get_country_name

logger = logging.getLogger(__name__)

used_flag_countries: dict = defaultdict(set)

_FLAG_TIME = {'easy': 90, 'normal': 60, 'hard': 40}


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


async def get_flag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    user_id = _uid(update)
    lang = _lang(update)
    difficulty = get_difficulty(user_id)
    timeout_sec = _FLAG_TIME.get(difficulty, 60)

    cancel_capital_job(chat_id)
    cancel_country_job(chat_id)
    cancel_flag_job(chat_id)
    active_country_games.pop(chat_id, None)
    active_capital_games.pop(chat_id, None)

    continent = get_continent_filter(user_id)
    pool = [c for c in COUNTRIES if continent == 'all' or COUNTRY_CONTINENTS.get(c) == continent]
    used = used_flag_countries[chat_id]
    available = [c for c in pool if c not in used]

    if not available:
        used_flag_countries[chat_id].clear()
        available = pool[:]

    if not available:
        await update.message.reply_text(t(lang, 'all_flags_played'), reply_markup=default_kb(lang, update.effective_chat.type in ("group","supergroup")))
        return

    country_uz = random.choice(available)
    used.add(country_uz)

    job = context.job_queue.run_once(
        callback=timeout_flag_guess,
        when=timeout_sec,
        data={'chat_id': chat_id, 'country': country_uz, 'lang': lang,
              'is_group': _is_group(update),
              'user_id': user_id if not _is_group(update) else ''},
        name=f"flag_timeout_{chat_id}",
    )
    active_flag_games[chat_id] = {
        'country': country_uz, 'attempts': 0,
        'hint_data': new_hint_data(), 'job': job,
    }

    flag = COUNTRY_FLAGS.get(country_uz, '🏴')
    progress = t(lang, 'progress', played=len(used), total=len(pool))

    if _is_group(update):
        msg = t(lang, 'flag_game_group', flag=flag)
    else:
        msg = t(lang, 'flag_game_private', flag=flag)

    await update.message.reply_text(
        f"{msg}\n\n{progress}", parse_mode='Markdown', reply_markup=guess_kb(lang)
    )
    logger.info("Flag game: chat=%s → %s [%s]", chat_id, country_uz, difficulty)


async def timeout_flag_guess(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    country_uz = data['country']
    lang = data.get('lang', 'uz')
    if chat_id in active_flag_games and active_flag_games[chat_id]['country'] == country_uz:
        del active_flag_games[chat_id]
        uid = data.get('user_id', '')
        if uid:
            record_result(uid, '', 'country', 'wrong')
            reset_streak(uid, '')
        flag = COUNTRY_FLAGS.get(country_uz, '🏴')
        country_display = get_country_name(country_uz, lang)
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=t(lang, 'timeout_flag', flag=flag, country=country_display),
            parse_mode='Markdown',
            reply_markup=default_kb(lang, data.get('is_group', False)),
        )
