"""Game modes: country-from-hint, country-from-capital, flag game."""
import html
import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

from data import (
    COUNTRIES, COUNTRIES_CAPITALS, COUNTRY_CONTINENTS,
    COUNTRY_FLAGS, COUNTRY_HINTS_UZ,
)
from database import (
    get_user_lang, get_display_name,
    get_difficulty, get_continent_filter,
)
from keyboards import default_kb, guess_kb, map_kb
from state import (
    active_country_games, active_capital_games, active_flag_games,
    used_country_countries, used_capital_countries,
    cancel_capital_job, cancel_country_job, cancel_flag_job,
    new_hint_data, user_game_chats,
)
from translations import t, get_hint, get_country_name

logger = logging.getLogger(__name__)

_CONTINENT_KEY = {
    'africa': 'region_africa', 'asia': 'region_asia', 'europe': 'region_europe',
    'north_america': 'region_north_america', 'south_america': 'region_south_america',
    'oceania': 'region_oceania',
}

# Seconds per difficulty level
_COUNTRY_TIME = {'easy': 120, 'normal': 90, 'hard': 60}
_FLAG_TIME    = {'easy': 90,  'normal': 60, 'hard': 40}
_CAPITAL_TIME = {'easy': 90,  'normal': 60, 'hard': 30}


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


def _filtered_pool(user_id: str) -> list[str]:
    continent = get_continent_filter(user_id)
    if continent == 'all':
        return COUNTRIES
    return [c for c in COUNTRIES if COUNTRY_CONTINENTS.get(c) == continent]


async def _next_hint(country_uz: str, lang: str, hint_data: dict) -> str:
    """Return the next progressive hint and advance the hint index."""
    from handlers.facts import fetch_wiki_sentences

    idx = hint_data['idx']
    hint_data['idx'] += 1

    if idx == 0:
        local = get_hint(country_uz, lang, COUNTRY_HINTS_UZ)
        return t(lang, 'hint_1', hint=local)

    # Fetch Wikipedia sentences on first web-hint request
    if not hint_data['fetched']:
        hint_data['wiki_sentences'] = await fetch_wiki_sentences(country_uz, lang)
        hint_data['fetched'] = True

    wiki = hint_data['wiki_sentences']
    wiki_idx = idx - 1  # wiki sentence offset

    if wiki_idx < len(wiki):
        return t(lang, 'hint_wiki', hint=wiki[wiki_idx])

    # After wiki sentences: flag → capital
    after_wiki = idx - 1 - len(wiki)
    if after_wiki == 0:
        continent_key = COUNTRY_CONTINENTS.get(country_uz, '')
        continent_label = t(lang, _CONTINENT_KEY.get(continent_key, 'region_all'))
        return t(lang, 'hint_continent', continent=continent_label)
    if after_wiki == 1:
        flag = COUNTRY_FLAGS.get(country_uz, '🏴')
        return t(lang, 'hint_flag', flag=flag)
    if after_wiki == 2:
        capital = COUNTRIES_CAPITALS.get(country_uz, '—')
        return t(lang, 'hint_capital', capital=capital)

    return t(lang, 'hint_exhausted')


# ---------------------------------------------------------------------------
# Country game
# ---------------------------------------------------------------------------

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    user_id = _uid(update)
    lang = _lang(update)
    difficulty = get_difficulty(user_id)

    cancel_capital_job(chat_id)
    cancel_country_job(chat_id)
    cancel_flag_job(chat_id)
    active_capital_games.pop(chat_id, None)
    active_flag_games.pop(chat_id, None)

    pool = _filtered_pool(user_id)
    used = used_country_countries[chat_id]
    available = [c for c in pool if c not in used]
    in_group = _is_group(update)
    if not available:
        await update.message.reply_text(t(lang, 'all_countries_played'), reply_markup=default_kb(lang, in_group))
        return

    country_uz = random.choice(available)
    used.add(country_uz)

    timeout_sec = _COUNTRY_TIME.get(difficulty, 90)
    job = context.job_queue.run_once(
        callback=timeout_country_guess,
        when=timeout_sec,
        data={'chat_id': chat_id, 'country': country_uz, 'lang': lang, 'is_group': in_group},
        name=f"country_timeout_{chat_id}",
    )
    active_country_games[chat_id] = {
        'country': country_uz, 'attempts': 0,
        'hint_data': new_hint_data(), 'job': job,
    }
    user_game_chats[user_id] = chat_id   # lets mini-app map find the game by user_id

    hint_text = get_hint(country_uz, lang, COUNTRY_HINTS_UZ)
    extra = ''
    if difficulty == 'easy':
        flag = COUNTRY_FLAGS.get(country_uz, '')
        extra = f'\n🚩 {flag}'

    progress = t(lang, 'progress', played=len(used), total=len(pool))
    if in_group:
        msg = t(lang, 'country_game_group', hint=hint_text) + extra
    else:
        msg = t(lang, 'country_game_private', hint=hint_text) + extra

    await update.message.reply_text(
        f"{msg}\n\n{progress}", parse_mode='Markdown', reply_markup=map_kb(lang, in_group)
    )
    logger.info("Country game: chat=%s → %s [%s]", chat_id, country_uz, difficulty)


async def timeout_country_guess(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    country_uz = data['country']
    lang = data.get('lang', 'uz')
    if chat_id in active_country_games and active_country_games[chat_id]['country'] == country_uz:
        del active_country_games[chat_id]
        # Clear user→chat mapping (user_id not available here, iterate to find)
        for uid, cid in list(user_game_chats.items()):
            if cid == chat_id:
                del user_game_chats[uid]
                break
        country_display = get_country_name(country_uz, lang)
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=t(lang, 'timeout_country', country=country_display),
            parse_mode='Markdown',
            reply_markup=default_kb(lang, data.get('is_group', False)),
        )


# ---------------------------------------------------------------------------
# Capital game
# ---------------------------------------------------------------------------

async def get_capital(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    user_id = _uid(update)
    lang = _lang(update)
    difficulty = get_difficulty(user_id)
    timeout_sec = _CAPITAL_TIME.get(difficulty, 60)

    cancel_capital_job(chat_id)
    cancel_country_job(chat_id)
    cancel_flag_job(chat_id)
    active_country_games.pop(chat_id, None)
    active_flag_games.pop(chat_id, None)

    pool = _filtered_pool(user_id)
    used = used_capital_countries[chat_id]
    available = [c for c in pool if c not in used]
    in_group = _is_group(update)
    if not available:
        await update.message.reply_text(t(lang, 'all_capitals_played'), reply_markup=default_kb(lang, in_group))
        return

    country_uz = random.choice(available)
    used.add(country_uz)
    capital = COUNTRIES_CAPITALS[country_uz]

    job = context.job_queue.run_once(
        callback=timeout_capital_guess,
        when=timeout_sec,
        data={'chat_id': chat_id, 'country': country_uz, 'lang': lang, 'is_group': in_group},
        name=f"timeout_{chat_id}",
    )
    active_capital_games[chat_id] = {'country': country_uz, 'capital': capital, 'job': job, 'attempts': 0}

    progress = t(lang, 'progress', played=len(used), total=len(pool))
    if in_group:
        msg = t(lang, 'capital_game_group', capital=capital)
    else:
        msg = t(lang, 'capital_game_private', capital=capital)

    await update.message.reply_text(
        f"{msg}\n\n{progress}", parse_mode='Markdown', reply_markup=guess_kb(lang)
    )
    logger.info("Capital game: chat=%s → %s (%s) [%s]", chat_id, country_uz, capital, difficulty)


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
            reply_markup=default_kb(lang, data.get('is_group', False)),
        )
        logger.info("Capital timeout: chat=%s — %s", chat_id, country_uz)


# ---------------------------------------------------------------------------
# Hint (shared across all game types)
# ---------------------------------------------------------------------------

async def hint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    lang = _lang(update)

    # Determine active game and hint_data
    game = None
    country_uz = None

    if chat_id in active_country_games:
        game = active_country_games[chat_id]
        country_uz = game['country']
    elif chat_id in active_flag_games:
        game = active_flag_games[chat_id]
        country_uz = game['country']
    elif chat_id in active_capital_games:
        # Capital game: only one hint (the hint text)
        country_uz = active_capital_games[chat_id]['country']
        hint_text = get_hint(country_uz, lang, COUNTRY_HINTS_UZ) or t(lang, 'hint_not_found')
        await update.message.reply_text(
            t(lang, 'hint_text', hint=hint_text),
            parse_mode='Markdown',
            reply_markup=guess_kb(lang),
        )
        return

    if country_uz and game is not None:
        in_group = _is_group(update)
        kb = map_kb(lang, in_group) if chat_id in active_country_games else guess_kb(lang)
        hint_msg = await _next_hint(country_uz, lang, game['hint_data'])
        await update.message.reply_text(hint_msg, parse_mode='Markdown', reply_markup=kb)
    else:
        await update.message.reply_text(t(lang, 'hint_no_game'), reply_markup=default_kb(lang, _is_group(update)))
