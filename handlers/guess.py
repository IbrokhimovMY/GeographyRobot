"""Handles free-text guesses and map WebApp selections."""
import json
import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from data import MAP_EN_TO_UZ, MAP_ANY_TO_UZ, COUNTRIES_SET, COUNTRY_FLAGS, COUNTRY_CURRENCIES
from database import (
    get_user_lang, get_display_name, record_result,
    increment_streak, reset_streak,
)
from keyboards import default_kb, guess_kb, map_kb
from state import (
    active_country_games, active_capital_games, active_flag_games, active_currency_games,
    cancel_capital_job, cancel_country_job, cancel_flag_job, cancel_currency_job,
    user_game_chats,
)
from translations import t, get_country_name

from handlers.game import get_country, get_capital, hint
from handlers.misc import stats, top, reset, help_command
from handlers.facts import daily_facts_command, _fetch_wiki_fact
from handlers.flag import get_flag, used_flag_countries
from handlers.info import info_command, info_lookup
from handlers.challenge import get_challenge, mark_solved
from handlers.currency import get_currency_game
from handlers.quiz import check_text_quiz_answer, start_variant_quiz, start_text_quiz
from handlers.poll_quiz import check_custom_text_answer
from handlers.invite import invite_command

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5

_BUTTON_ROUTES = None


def _build_routes():
    from translations import STRINGS
    routes = {}
    for lang in ('uz', 'ru', 'en'):
        s = STRINGS[lang]
        # Use _fix_apos so buttons with O'/G' match regardless of apostrophe type
        routes[_fix_apos(s['btn_country']).lower()]      = get_country
        routes[_fix_apos(s['btn_capital']).lower()]      = get_capital
        routes[_fix_apos(s['btn_hint']).lower()]         = hint
        routes[_fix_apos(s['btn_top']).lower()]          = top
        routes[_fix_apos(s['btn_stats']).lower()]        = stats
        routes[_fix_apos(s['btn_reset']).lower()]        = reset
        routes[_fix_apos(s['btn_help']).lower()]         = help_command
        routes[_fix_apos(s['btn_daily_facts']).lower()]  = daily_facts_command
        routes[_fix_apos(s['btn_flag']).lower()]         = get_flag
        routes[_fix_apos(s['btn_challenge']).lower()]    = get_challenge
        routes[_fix_apos(s['btn_info']).lower()]         = info_command
        routes[_fix_apos(s['btn_currency']).lower()]     = get_currency_game
        routes[_fix_apos(s['btn_region']).lower()]       = _region_btn
        routes[_fix_apos(s['btn_difficulty']).lower()]   = _difficulty_btn
        routes[_fix_apos(s['btn_quiz1']).lower()]        = start_variant_quiz
        routes[_fix_apos(s['btn_quiz2']).lower()]        = start_text_quiz
        routes[_fix_apos(s['btn_invite']).lower()]       = invite_command
    return routes


async def _region_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers.settings import region_command
    await region_command(update, context)


async def _difficulty_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from handlers.settings import difficulty_command
    await difficulty_command(update, context)


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


def _fix_apos(s: str) -> str:
    """Normalize fancy apostrophes (mobile keyboards) to standard ASCII '."""
    for ch in ('‘', '’', 'ʻ', 'ʼ', 'ʹ', '`', '´', '′'):
        s = s.replace(ch, "'")
    return s


def _normalize(text: str) -> str:
    text = _fix_apos(text.strip())
    return MAP_ANY_TO_UZ.get(text.lower(), text)


def _streak_suffix(user_id: str, username: str, lang: str) -> str:
    streak, is_best = increment_streak(user_id, username)
    if streak < 2:
        return ''
    if is_best and streak > 2:
        return t(lang, 'streak_best', n=streak)
    return t(lang, 'streak_new', n=streak)


async def _send_wiki_fact_bg(context: ContextTypes.DEFAULT_TYPE, chat_id: int,
                              country_uz: str, lang: str) -> None:
    fact = await _fetch_wiki_fact(country_uz, lang)
    if fact:
        country_display = html.escape(get_country_name(country_uz, lang))
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📖 <b>{country_display}</b>\n\n{html.escape(fact)}",
            parse_mode='HTML',
        )


def _schedule_fact(context: ContextTypes.DEFAULT_TYPE, chat_id: int,
                   country_uz: str, lang: str) -> None:
    context.application.create_task(
        _send_wiki_fact_bg(context, chat_id, country_uz, lang)
    )


async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global _BUTTON_ROUTES
    if _BUTTON_ROUTES is None:
        _BUTTON_ROUTES = _build_routes()

    text = update.message.text.strip()
    if len(text) > 100:
        return

    # Info mode: user is answering the info prompt
    if context.user_data.get('awaiting_info'):
        await info_lookup(update, context)
        return

    route = _BUTTON_ROUTES.get(_fix_apos(text).lower())
    if route:
        await route(update, context)
        return

    chat_id = _chat_id(update)
    user_id = _uid(update)
    username = _uname(update)
    lang = _lang(update)
    in_group = _is_group(update)
    guess_uz = _normalize(text)

    # --- Custom text test quiz ---
    if await check_custom_text_answer(chat_id, user_id, username, text, update, context):
        return

    # --- Text quiz (group quiz type 2) ---
    if await check_text_quiz_answer(chat_id, user_id, username, guess_uz, update, context):
        return

    # --- Flag game ---
    if chat_id in active_flag_games:
        game = active_flag_games[chat_id]
        correct_uz = game['country']
        if guess_uz.lower() == correct_uz.lower():
            cancel_flag_job(chat_id)
            del active_flag_games[chat_id]
            name = _player_name(update)
            flag = COUNTRY_FLAGS.get(correct_uz, '🏴')
            correct_display = get_country_name(correct_uz, lang)
            record_result(user_id, username, 'country', 'correct')
            streak_sfx = _streak_suffix(user_id, username, lang)
            if in_group:
                msg = t(lang, 'correct_flag_group',
                        name=html.escape(name),
                        country=html.escape(correct_display), flag=flag) + streak_sfx
            else:
                msg = t(lang, 'correct_flag_private',
                        country=html.escape(correct_display), flag=flag) + streak_sfx
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang, in_group))
            _schedule_fact(context, update.effective_chat.id, correct_uz, lang)
        else:
            game['attempts'] += 1
            if game['attempts'] >= MAX_ATTEMPTS:
                cancel_flag_job(chat_id)
                del active_flag_games[chat_id]
                record_result(user_id, username, 'country', 'wrong')
                reset_streak(user_id, username)
                flag = COUNTRY_FLAGS.get(correct_uz, '🏴')
                correct_display = get_country_name(correct_uz, lang)
                await update.message.reply_text(
                    t(lang, 'game_failed', country=html.escape(correct_display)),
                    parse_mode='HTML', reply_markup=default_kb(lang, in_group),
                )
            else:
                reset_streak(user_id, username)
                remaining = MAX_ATTEMPTS - game['attempts']
                if in_group:
                    await update.message.reply_text(f"❌ {remaining}🎯")
                else:
                    await update.message.reply_text(
                        f"{t(lang, 'wrong_flag')} ({remaining}🎯)",
                        reply_markup=guess_kb(lang),
                    )
        return

    # --- Currency game ---
    if chat_id in active_currency_games:
        game = active_currency_games[chat_id]
        correct_uz = game['country']
        if guess_uz.lower() == correct_uz.lower():
            cancel_currency_job(chat_id)
            del active_currency_games[chat_id]
            flag = COUNTRY_FLAGS.get(correct_uz, '🏴')
            correct_display = get_country_name(correct_uz, lang)
            cur_name, cur_code = COUNTRY_CURRENCIES.get(correct_uz, ('', ''))
            record_result(user_id, username, 'country', 'correct')
            streak_sfx = _streak_suffix(user_id, username, lang)
            msg = t(lang, 'correct_currency',
                    country=html.escape(correct_display), flag=flag,
                    currency=cur_name, code=cur_code) + streak_sfx
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang, in_group))
            _schedule_fact(context, update.effective_chat.id, correct_uz, lang)
        else:
            game['attempts'] += 1
            if game['attempts'] >= MAX_ATTEMPTS:
                cancel_currency_job(chat_id)
                del active_currency_games[chat_id]
                correct_display = get_country_name(correct_uz, lang)
                cur_name, cur_code = COUNTRY_CURRENCIES.get(correct_uz, ('', ''))
                record_result(user_id, username, 'country', 'wrong')
                reset_streak(user_id, username)
                await update.message.reply_text(
                    t(lang, 'game_failed', country=html.escape(correct_display)),
                    parse_mode='HTML', reply_markup=default_kb(lang, in_group),
                )
            else:
                reset_streak(user_id, username)
                remaining = MAX_ATTEMPTS - game['attempts']
                if in_group:
                    await update.message.reply_text(f"❌ {remaining}🎯")
                else:
                    await update.message.reply_text(
                        f"{t(lang, 'wrong_country')} ({remaining}🎯)",
                        reply_markup=guess_kb(lang),
                    )
        return

    # --- Country game ---
    if chat_id in active_country_games:
        game = active_country_games[chat_id]
        correct_uz = game['country']
        is_challenge = game.get('challenge', False)
        if guess_uz.lower() == correct_uz.lower():
            cancel_country_job(chat_id)
            del active_country_games[chat_id]
            user_game_chats.pop(user_id, None)
            name = _player_name(update)
            correct_display = get_country_name(correct_uz, lang)
            record_result(user_id, username, 'country', 'correct')
            streak_sfx = _streak_suffix(user_id, username, lang)
            if is_challenge:
                mark_solved(user_id)
                if in_group:
                    msg = t(lang, 'challenge_correct',
                            name=html.escape(name),
                            country=html.escape(correct_display)) + streak_sfx
                else:
                    msg = t(lang, 'challenge_correct_private',
                            country=html.escape(correct_display)) + streak_sfx
            elif in_group:
                msg = t(lang, 'correct_country_group',
                        name=html.escape(name),
                        country=html.escape(correct_display)) + streak_sfx
            else:
                msg = t(lang, 'correct_country_private',
                        name=html.escape(name),
                        country=html.escape(correct_display)) + streak_sfx
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang, in_group))
            _schedule_fact(context, update.effective_chat.id, correct_uz, lang)
            logger.info("Country correct: chat=%s user=%s — %s", chat_id, user_id, correct_uz)
        else:
            game['attempts'] += 1
            if game['attempts'] >= MAX_ATTEMPTS:
                cancel_country_job(chat_id)
                del active_country_games[chat_id]
                user_game_chats.pop(user_id, None)
                record_result(user_id, username, 'country', 'wrong')
                reset_streak(user_id, username)
                correct_display = get_country_name(correct_uz, lang)
                await update.message.reply_text(
                    t(lang, 'game_failed', country=html.escape(correct_display)),
                    parse_mode='HTML', reply_markup=default_kb(lang, in_group),
                )
            else:
                reset_streak(user_id, username)
                remaining = MAX_ATTEMPTS - game['attempts']
                if in_group:
                    await update.message.reply_text(f"❌ {remaining}🎯")
                else:
                    await update.message.reply_text(
                        f"{t(lang, 'wrong_country')} ({remaining}🎯)",
                        reply_markup=guess_kb(lang),
                    )
        return

    # --- Capital game ---
    if chat_id in active_capital_games:
        game = active_capital_games[chat_id]
        correct_uz = game['country']
        if guess_uz.lower() == correct_uz.lower():
            cancel_capital_job(chat_id)
            record_result(user_id, username, 'capital', 'correct')
            del active_capital_games[chat_id]
            name = _player_name(update)
            correct_display = get_country_name(correct_uz, lang)
            streak_sfx = _streak_suffix(user_id, username, lang)
            if in_group:
                msg = t(lang, 'correct_capital_group',
                        name=html.escape(name),
                        country=html.escape(correct_display)) + streak_sfx
            else:
                msg = t(lang, 'correct_capital_private',
                        name=html.escape(name),
                        country=html.escape(correct_display)) + streak_sfx
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang, in_group))
            _schedule_fact(context, update.effective_chat.id, correct_uz, lang)
            logger.info("Capital correct: chat=%s user=%s — %s", chat_id, user_id, correct_uz)
        else:
            game['attempts'] = game.get('attempts', 0) + 1
            reset_streak(user_id, username)
            if game['attempts'] >= MAX_ATTEMPTS:
                cancel_capital_job(chat_id)
                del active_capital_games[chat_id]
                record_result(user_id, username, 'capital', 'wrong')
                correct_display = get_country_name(correct_uz, lang)
                await update.message.reply_text(
                    t(lang, 'game_failed', country=html.escape(correct_display)),
                    parse_mode='HTML', reply_markup=default_kb(lang, in_group),
                )
            else:
                record_result(user_id, username, 'capital', 'wrong')
                remaining = MAX_ATTEMPTS - game['attempts']
                if in_group:
                    await update.message.reply_text(f"❌ {remaining}🎯")
                else:
                    await update.message.reply_text(
                        f"{t(lang, 'wrong_capital')} ({remaining}🎯)",
                        reply_markup=guess_kb(lang),
                    )
        return

    # Don't show "no active game" if a text quiz is running — wrong answers are silent
    from handlers.quiz import active_text_quizzes
    from handlers.poll_quiz import active_custom_text_quizzes
    if chat_id in active_text_quizzes or chat_id in active_custom_text_quizzes:
        return

    if not in_group:
        await update.message.reply_text(t(lang, 'no_active_game'), reply_markup=default_kb(lang, in_group))


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

    game = active_country_games[chat_id]
    correct_uz = game['country']
    name = _player_name(update)
    in_group = _is_group(update)

    selected_uz = MAP_EN_TO_UZ.get(selected_en, selected_en)
    correct_display = get_country_name(correct_uz, lang)
    selected_display = (
        get_country_name(selected_uz, lang) if selected_uz in COUNTRIES_SET else selected_en
    )

    if selected_uz.lower() == correct_uz.lower():
        cancel_country_job(chat_id)
        is_challenge = game.get('challenge', False)
        record_result(user_id, username, 'country', 'correct')
        del active_country_games[chat_id]
        user_game_chats.pop(user_id, None)
        streak_sfx = _streak_suffix(user_id, username, lang)
        if is_challenge:
            mark_solved(user_id)
        if in_group:
            msg = t(lang, 'map_correct_group',
                    name=html.escape(name), country=html.escape(correct_display)) + streak_sfx
        else:
            msg = t(lang, 'map_correct_private',
                    country=html.escape(correct_display)) + streak_sfx
        await context.bot.send_message(
            chat_id=int(chat_id), text=msg, parse_mode='HTML', reply_markup=default_kb(lang)
        )
        _schedule_fact(context, int(chat_id), correct_uz, lang)
        logger.info("Map correct: chat=%s user=%s — %s", chat_id, user_id, correct_uz)
    else:
        game['attempts'] = game.get('attempts', 0) + 1
        if game['attempts'] >= MAX_ATTEMPTS:
            cancel_country_job(chat_id)
            del active_country_games[chat_id]
            user_game_chats.pop(user_id, None)
            record_result(user_id, username, 'country', 'wrong')
            reset_streak(user_id, username)
            await context.bot.send_message(
                chat_id=int(chat_id),
                text=t(lang, 'game_failed', country=html.escape(correct_display)),
                parse_mode='HTML', reply_markup=default_kb(lang, in_group),
            )
        else:
            reset_streak(user_id, username)
            record_result(user_id, username, 'country', 'wrong')
            remaining = MAX_ATTEMPTS - game['attempts']
            await context.bot.send_message(
                chat_id=int(chat_id),
                text=f"{t(lang, 'map_wrong', selected=html.escape(selected_display))} ({remaining}🎯)",
                parse_mode='HTML',
                reply_markup=guess_kb(lang),
            )
