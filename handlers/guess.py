"""Handles free-text guesses and map WebApp selections."""
import json
import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from data import MAP_EN_TO_UZ, MAP_ANY_TO_UZ, COUNTRIES_SET
from database import get_user_lang, get_display_name, record_result
from keyboards import default_kb, guess_kb, map_kb
from state import active_country_games, active_capital_games, cancel_capital_job
from translations import t, get_country_name

from handlers.game import get_country, get_capital, hint
from handlers.misc import stats, top, reset, help_command

logger = logging.getLogger(__name__)

# Button text from all languages → handler function
_BUTTON_ROUTES = None   # built lazily to avoid circular dependency on STRINGS


def _build_routes():
    from translations import STRINGS
    routes = {}
    for lang in ('uz', 'ru', 'en'):
        s = STRINGS[lang]
        routes[s['btn_country'].lower()] = get_country
        routes[s['btn_capital'].lower()] = get_capital
        routes[s['btn_hint'].lower()]    = hint
        routes[s['btn_top'].lower()]     = top
        routes[s['btn_stats'].lower()]   = stats
        routes[s['btn_reset'].lower()]   = reset
        routes[s['btn_help'].lower()]    = help_command
    return routes


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


def _uname(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)


def _lang(update: Update) -> str:
    return get_user_lang(_uid(update))


def _player_name(update: Update) -> str:
    return get_display_name(_uid(update), _uname(update))


def _chat_id(update: Update) -> str:
    return str(update.effective_chat.id)


def _is_group(update: Update) -> bool:
    return update.effective_chat.type in ('group', 'supergroup')


def _normalize(text: str) -> str:
    """Return the UZ internal country name matching any-language input, or the original text."""
    return MAP_ANY_TO_UZ.get(text.strip().lower(), text.strip())


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global _BUTTON_ROUTES
    if _BUTTON_ROUTES is None:
        _BUTTON_ROUTES = _build_routes()

    text = update.message.text.strip()
    if len(text) > 100:
        return

    # Route keyboard button presses
    route = _BUTTON_ROUTES.get(text.lower())
    if route:
        await route(update, context)
        return

    chat_id = _chat_id(update)
    user_id = _uid(update)
    username = _uname(update)
    lang = _lang(update)
    in_group = _is_group(update)

    guess_uz = _normalize(text)

    # --- Country game ---
    if chat_id in active_country_games:
        correct_uz = active_country_games[chat_id]['country']
        if guess_uz.lower() == correct_uz.lower():
            record_result(user_id, username, 'country', 'correct')
            del active_country_games[chat_id]
            name = _player_name(update)
            correct_display = get_country_name(correct_uz, lang)
            if in_group:
                msg = t(lang, 'correct_country_group',
                        name=html.escape(name), country=html.escape(correct_display))
            else:
                msg = t(lang, 'correct_country_private',
                        name=html.escape(name), country=html.escape(correct_display))
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang))
            logger.info("Country correct: chat=%s user=%s — %s", chat_id, user_id, correct_uz)
        else:
            if not in_group:
                await update.message.reply_text(t(lang, 'wrong_country'), reply_markup=guess_kb(lang))
        return

    # --- Capital game ---
    if chat_id in active_capital_games:
        correct_uz = active_capital_games[chat_id]['country']
        if guess_uz.lower() == correct_uz.lower():
            cancel_capital_job(chat_id)
            record_result(user_id, username, 'capital', 'correct')
            del active_capital_games[chat_id]
            name = _player_name(update)
            correct_display = get_country_name(correct_uz, lang)
            if in_group:
                msg = t(lang, 'correct_capital_group',
                        name=html.escape(name), country=html.escape(correct_display))
            else:
                msg = t(lang, 'correct_capital_private',
                        name=html.escape(name), country=html.escape(correct_display))
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang))
            logger.info("Capital correct: chat=%s user=%s — %s", chat_id, user_id, correct_uz)
        else:
            record_result(user_id, username, 'capital', 'wrong')
            if not in_group:
                await update.message.reply_text(t(lang, 'wrong_capital'), reply_markup=guess_kb(lang))
        return

    if not in_group:
        await update.message.reply_text(t(lang, 'no_active_game'), reply_markup=default_kb(lang))


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    user_id = _uid(update)
    username = _uname(update)
    lang = _lang(update)
    raw = update.effective_message.web_app_data.data

    try:
        selected_en = json.loads(raw)['country']
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("WebApp error: %s — %s", user_id, exc)
        await context.bot.send_message(
            chat_id=int(chat_id), text=t(lang, 'webapp_error'), reply_markup=map_kb(lang)
        )
        return

    if chat_id not in active_country_games:
        await context.bot.send_message(
            chat_id=int(chat_id), text=t(lang, 'map_no_game'), reply_markup=default_kb(lang)
        )
        return

    correct_uz = active_country_games[chat_id]['country']
    name = _player_name(update)
    in_group = _is_group(update)

    selected_uz = MAP_EN_TO_UZ.get(selected_en, selected_en)
    correct_display = get_country_name(correct_uz, lang)
    selected_display = (
        get_country_name(selected_uz, lang) if selected_uz in COUNTRIES_SET else selected_en
    )

    if selected_uz.lower() == correct_uz.lower():
        record_result(user_id, username, 'country', 'correct')
        del active_country_games[chat_id]
        if in_group:
            msg = t(lang, 'map_correct_group',
                    name=html.escape(name), country=html.escape(correct_display))
        else:
            msg = t(lang, 'map_correct_private',
                    name=html.escape(name), country=html.escape(correct_display))
        await context.bot.send_message(
            chat_id=int(chat_id), text=msg, parse_mode='HTML', reply_markup=default_kb(lang)
        )
        logger.info("Map correct: chat=%s user=%s — %s", chat_id, user_id, correct_uz)
    else:
        record_result(user_id, username, 'country', 'wrong')
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=t(lang, 'map_wrong', selected=html.escape(selected_display)),
            parse_mode='HTML',
            reply_markup=map_kb(lang),
        )
