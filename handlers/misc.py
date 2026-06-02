"""Stats, top, reset, help, and /language command for returning users."""
import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_user_lang, get_display_name, set_user_lang,
    get_stats, get_top_users, get_user_count,
)
from keyboards import default_kb, CHANGE_LANG_KB
from state import (
    active_country_games, active_capital_games, active_flag_games, active_currency_games,
    cancel_capital_job, cancel_country_job, cancel_flag_job, cancel_currency_job,
    used_country_countries, used_capital_countries,
)
from handlers.flag import used_flag_countries
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

    total_correct = s['correct_country'] + s['correct_capital']
    total_wrong   = s['wrong_country'] + s['wrong_capital']
    total_timeout = s['timeout_capital']
    total = total_correct + total_wrong + total_timeout

    correct_pct = round(total_correct / total * 100) if total else 0
    wrong_pct   = round(total_wrong   / total * 100) if total else 0
    timeout_pct = round(total_timeout / total * 100) if total else 0

    text = (
        t(lang, 'stats_header',  name=html.escape(name))
        + t(lang, 'stats_total',   total=total)
        + t(lang, 'stats_correct', correct=total_correct, pct=correct_pct)
        + t(lang, 'stats_wrong',   wrong=total_wrong,     wpct=wrong_pct)
        + t(lang, 'stats_timeout', timeout=total_timeout, tpct=timeout_pct)
        + t(lang, 'stats_streak',  streak=s['streak'],    best=s['best_streak'])
    )
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=default_kb(lang, update.effective_chat.type in ("group","supergroup")))


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(update)
    rows = get_top_users(10)
    if not rows:
        await update.message.reply_text(t(lang, 'top_no_players'), reply_markup=default_kb(lang, update.effective_chat.type in ("group","supergroup")))
        return

    medals = ['🥇', '🥈', '🥉']
    lines = [t(lang, 'top_header')]
    for i, (name, total_correct, total_games) in enumerate(rows, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        pct = round(total_correct / total_games * 100) if total_games else 0
        lines.append(t(lang, 'top_entry',
                       medal=medal, name=html.escape(str(name)),
                       pct=pct, correct=total_correct, total=total_games))

    await update.message.reply_text('\n'.join(lines), parse_mode='HTML', reply_markup=default_kb(lang, update.effective_chat.type in ("group","supergroup")))


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    lang = _lang(update)
    in_group = update.effective_chat.type in ('group', 'supergroup')
    cancel_capital_job(chat_id)
    cancel_country_job(chat_id)
    cancel_flag_job(chat_id)
    cancel_currency_job(chat_id)
    active_country_games.pop(chat_id, None)
    # Clear user→chat game mapping for this chat
    from state import user_game_chats
    for uid, cid in list(user_game_chats.items()):
        if cid == chat_id:
            del user_game_chats[uid]
    active_capital_games.pop(chat_id, None)
    active_flag_games.pop(chat_id, None)
    active_currency_games.pop(chat_id, None)
    used_capital_countries[chat_id].clear()
    used_country_countries[chat_id].clear()
    used_flag_countries[chat_id].clear()
    # Also stop active quizzes
    from handlers.quiz import active_variant_quizzes, active_text_quizzes
    for d in (active_variant_quizzes, active_text_quizzes):
        q = d.pop(chat_id, None)
        if q and q.get('job'):
            q['job'].schedule_removal()
    logger.info("Reset: chat=%s by %s", chat_id, _uname(update))
    await update.message.reply_text(t(lang, 'reset_done'), reply_markup=default_kb(lang, in_group))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(update)
    await update.message.reply_text(t(lang, 'help_text'), reply_markup=default_kb(lang, update.effective_chat.type in ("group","supergroup")))


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


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin contact information."""
    lang = get_user_lang(str(update.effective_user.id))
    msg = {
        'uz': "👨‍💼 <b>Admin bo'limi</b>\n\nSavol, taklif yoki xato haqida xabar berish uchun:\n👉 @IbrokhimMY",
        'ru': "👨‍💼 <b>Раздел Admin</b>\n\nПо вопросам, предложениям или ошибкам:\n👉 @IbrokhimMY",
        'en': "👨‍💼 <b>Admin Section</b>\n\nFor questions, suggestions or bug reports:\n👉 @IbrokhimMY",
    }.get(lang, "👨‍💼 <b>Admin</b>\n\n👉 @IbrokhimMY")
    in_group = update.effective_chat.type in ('group', 'supergroup')
    await update.message.reply_text(msg, parse_mode='HTML',
                                    reply_markup=default_kb(lang, in_group))


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/users — show total user statistics (admin only)."""
    counts = get_user_count()
    text = (
        f"👥 <b>Bot statistikasi</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{counts['total']}</b>\n"
        f"🏠 Ulangan guruhlar: <b>{counts['groups']}</b>\n"
        f"🎮 Faol o'yinchilar: <b>{counts['active']}</b>\n"
        f"📅 Kunlik faktlar obunasi: <b>{counts['subscribers']}</b>"
    )
    await update.message.reply_text(text, parse_mode='HTML')
