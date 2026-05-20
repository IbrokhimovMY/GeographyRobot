"""Handlers for the two game modes: country-from-hint and country-from-capital."""
import random
import sqlite3
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import DB_PATH
from data import COUNTRIES, COUNTRIES_CAPITALS
from database import get_user_lang, get_display_name, _ensure_user
from keyboards import default_kb, guess_kb, map_kb
from state import (
    active_country_games, active_capital_games,
    used_country_countries, used_capital_countries,
    cancel_capital_job,
)
from translations import t, get_hint, get_country_name
from data import COUNTRY_HINTS_UZ

logger = logging.getLogger(__name__)


def _chat_id(update: Update) -> str:
    return str(update.effective_chat.id)


def _is_group(update: Update) -> bool:
    return update.effective_chat.type in ('group', 'supergroup')


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


def _uname(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)


def _lang(update: Update) -> str:
    return get_user_lang(_uid(update))


def _player_name(update: Update) -> str:
    return get_display_name(_uid(update), _uname(update))


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    lang = _lang(update)

    cancel_capital_job(chat_id)

    used = used_country_countries[chat_id]
    available = [c for c in COUNTRIES if c not in used]
    if not available:
        await update.message.reply_text(
            t(lang, 'all_countries_played'), reply_markup=default_kb(lang)
        )
        return

    country_uz = random.choice(available)
    used.add(country_uz)
    active_country_games[chat_id] = {'country': country_uz}

    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, _uid(update), _uname(update))

    hint_text = get_hint(country_uz, lang, COUNTRY_HINTS_UZ)
    if _is_group(update):
        msg = t(lang, 'country_game_group', hint=hint_text)
    else:
        msg = t(lang, 'country_game_private', hint=hint_text)

    await update.message.reply_text(
        msg, parse_mode='Markdown', reply_markup=map_kb(lang)
    )
    logger.info("Country game: chat=%s → %s", chat_id, country_uz)


async def get_capital(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    lang = _lang(update)

    cancel_capital_job(chat_id)

    used = used_capital_countries[chat_id]
    available = [c for c in COUNTRIES if c not in used]
    if not available:
        await update.message.reply_text(
            t(lang, 'all_capitals_played'), reply_markup=default_kb(lang)
        )
        return

    country_uz = random.choice(available)
    used.add(country_uz)
    capital = COUNTRIES_CAPITALS[country_uz]

    active_capital_games[chat_id] = {'country': country_uz, 'capital': capital, 'job': None}

    with sqlite3.connect(DB_PATH) as conn:
        _ensure_user(conn, _uid(update), _uname(update))

    job = context.job_queue.run_once(
        callback=timeout_capital_guess,
        when=60,
        data={'chat_id': chat_id, 'country': country_uz, 'lang': lang},
        name=f"timeout_{chat_id}",
    )
    active_capital_games[chat_id]['job'] = job

    if _is_group(update):
        msg = t(lang, 'capital_game_group', capital=capital)
    else:
        msg = t(lang, 'capital_game_private', capital=capital)

    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=guess_kb(lang))
    logger.info("Capital game: chat=%s → %s (%s)", chat_id, country_uz, capital)


async def timeout_capital_guess(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    country_uz = data['country']
    lang = data.get('lang', 'uz')

    if chat_id in active_capital_games and active_capital_games[chat_id]['country'] == country_uz:
        del active_capital_games[chat_id]
        country_display = get_country_name(country_uz, lang)
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=t(lang, 'timeout', country=country_display),
            parse_mode='Markdown',
            reply_markup=default_kb(lang),
        )
        logger.info("Timeout: chat=%s — %s", chat_id, country_uz)


async def hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    lang = _lang(update)

    country_uz = None
    if chat_id in active_country_games:
        country_uz = active_country_games[chat_id]['country']
    elif chat_id in active_capital_games:
        country_uz = active_capital_games[chat_id]['country']

    if country_uz:
        hint_text = get_hint(country_uz, lang, COUNTRY_HINTS_UZ) or t(lang, 'hint_not_found')
        await update.message.reply_text(
            t(lang, 'hint_text', hint=hint_text),
            parse_mode='Markdown',
            reply_markup=guess_kb(lang),
        )
    else:
        await update.message.reply_text(
            t(lang, 'hint_no_game'), reply_markup=default_kb(lang)
        )
