"""Handlers for region filter and difficulty inline keyboard callbacks."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import get_user_lang, set_continent_filter, set_difficulty
from keyboards import default_kb, continent_kb, difficulty_kb
from translations import t

logger = logging.getLogger(__name__)

_REGION_KEYS = {
    'region_all': 'region_all',
    'region_africa': 'region_africa', 'region_asia': 'region_asia',
    'region_europe': 'region_europe', 'region_north_america': 'region_north_america',
    'region_south_america': 'region_south_america', 'region_oceania': 'region_oceania',
}

_DIFF_LABELS = {
    'easy': 'difficulty_easy_label',
    'normal': 'difficulty_normal_label',
    'hard': 'difficulty_hard_label',
}


def _uid(q) -> str:
    return str(q.from_user.id)


def _uname(q) -> str:
    u = q.from_user
    return u.username or u.first_name or str(u.id)


async def region_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(str(update.effective_user.id))
    await update.message.reply_text(t(lang, 'region_select'), reply_markup=continent_kb(lang))


async def region_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = _uid(query)
    username = _uname(query)
    lang = get_user_lang(user_id)

    continent = query.data[len('region_'):]  # strip 'region_' prefix
    set_continent_filter(user_id, username, continent)

    label_key = _REGION_KEYS.get(query.data, 'region_all')
    region_label = t(lang, label_key)
    await query.edit_message_text(t(lang, 'region_set', region=region_label), parse_mode='HTML')
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=t(lang, 'welcome'),
        reply_markup=default_kb(lang),
    )


async def difficulty_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_user_lang(str(update.effective_user.id))
    await update.message.reply_text(t(lang, 'difficulty_select'), reply_markup=difficulty_kb(lang))


async def difficulty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = _uid(query)
    username = _uname(query)
    lang = get_user_lang(user_id)

    level = query.data[len('diff_'):]  # strip 'diff_' prefix → easy/normal/hard
    set_difficulty(user_id, username, level)

    label = t(lang, _DIFF_LABELS.get(level, 'difficulty_normal_label'))
    await query.edit_message_text(t(lang, 'difficulty_set', level=label), parse_mode='HTML')
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=t(lang, 'welcome'),
        reply_markup=default_kb(lang),
    )
