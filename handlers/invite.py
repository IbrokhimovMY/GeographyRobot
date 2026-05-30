"""Referral / invite-friends feature."""
import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from database import get_user_lang, get_referral_count
from keyboards import default_kb
from translations import t

logger = logging.getLogger(__name__)


def _uid(u: Update) -> str:
    return str(u.effective_user.id)


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = _uid(update)
    lang = get_user_lang(user_id)
    in_group = update.effective_chat.type in ('group', 'supergroup')

    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    count = get_referral_count(user_id)

    await update.message.reply_text(
        t(lang, 'invite_text', link=link, count=count),
        parse_mode='HTML',
        reply_markup=default_kb(lang, in_group),
    )
    logger.info("Invite shown: user=%s count=%d", user_id, count)
