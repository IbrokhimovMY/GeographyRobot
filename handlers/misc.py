"""Stats, top, reset, help, and /language command for returning users."""
import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_user_lang, get_display_name, set_user_lang,
    get_stats, get_top_users,
)
from keyboards import default_kb, CHANGE_LANG_KB
from state import active_country_games, active_capital_games, cancel_capital_job
from state import used_country_countries, used_capital_countries
from translations import t

logger = logging.getLogger(__name__)


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


def _uname(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)


def _lang(update: Update) -> str:
    return get_user_lang(_uid(update))


def _player_name(update: Update) -> str:
    return get_display_name(_uid(update), _uname(update))


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = _uid(update)
    username = _uname(update)
    lang = _lang(update)
    name = _player_name(update)
    s = get_stats(user_id, username)

    total_country = s['correct_country'] + s['wrong_country']
    total_capital = s['correct_capital'] + s['wrong_capital'] + s['timeout_capital']
    country_pct = round(s['correct_country'] / total_country * 100) if total_country else 0
    capital_pct = round(s['correct_capital'] / total_capital * 100) if total_capital else 0

    text = (
        t(lang, 'stats_header', name=html.escape(name))
        + t(lang, 'stats_country',
            correct=s['correct_country'], wrong=s['wrong_country'], pct=country_pct)
        + t(lang, 'stats_capital',
            correct=s['correct_capital'], wrong=s['wrong_capital'],
            timeout=s['timeout_capital'], pct=capital_pct)
    )
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=default_kb(lang))


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(update)
    rows = get_top_users(10)
    if not rows:
        await update.message.reply_text(t(lang, 'top_no_players'), reply_markup=default_kb(lang))
        return

    medals = ['🥇', '🥈', '🥉']
    lines = [t(lang, 'top_header')]
    for i, (name, cc, cap, total) in enumerate(rows, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        lines.append(t(lang, 'top_entry',
                       medal=medal, name=html.escape(str(name)),
                       total=total, cc=cc, cap=cap))

    await update.message.reply_text('\n'.join(lines), parse_mode='HTML', reply_markup=default_kb(lang))


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    lang = _lang(update)
    cancel_capital_job(chat_id)
    active_country_games.pop(chat_id, None)
    active_capital_games.pop(chat_id, None)
    used_capital_countries[chat_id].clear()
    used_country_countries[chat_id].clear()
    logger.info("Reset: chat=%s by %s", chat_id, _uname(update))
    await update.message.reply_text(t(lang, 'reset_done'), reply_markup=default_kb(lang))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(update)
    await update.message.reply_text(t(lang, 'help_text'), reply_markup=default_kb(lang))


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allow returning users to change language without re-registering."""
    lang = _lang(update)
    await update.message.reply_text(t(lang, 'language_select'), reply_markup=CHANGE_LANG_KB)


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for the /language inline keyboard (returning users only)."""
    query = update.callback_query
    await query.answer()

    lang_map = {'lang_uz': 'uz', 'lang_ru': 'ru', 'lang_en': 'en'}
    new_lang = lang_map.get(query.data)
    if not new_lang:
        return

    user_id = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name or user_id
    set_user_lang(user_id, username, new_lang)

    await query.edit_message_text(t(new_lang, 'language_set'))
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=t(new_lang, 'welcome'),
        reply_markup=default_kb(new_lang),
    )
