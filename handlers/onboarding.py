"""
Onboarding flow for new users:
  /start → language inline keyboard  →  "Enter your name:"  →  main keyboard

Returning users who already have a display_name skip straight to the main keyboard.
"""
import html
import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from database import get_display_name, get_user_lang, set_user_lang, set_display_name, add_referral
from keyboards import ONBOARD_LANG_KB, default_kb
from translations import t

logger = logging.getLogger(__name__)

# ConversationHandler states
LANG, NAME = range(2)


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


def _uname(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = _uid(update)

    # Detect referral parameter: /start ref_USERID
    if context.args:
        arg = context.args[0]
        if arg.startswith('ref_'):
            referrer_id = arg[4:]
            if referrer_id != user_id:          # can't refer yourself
                context.user_data['referrer_id'] = referrer_id

    await update.message.reply_text(
        t('uz', 'onboard_choose_lang'),
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text('👇', reply_markup=ONBOARD_LANG_KB)
    return LANG


async def lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    lang_map = {'onboard_uz': 'uz', 'onboard_ru': 'ru', 'onboard_en': 'en'}
    lang = lang_map.get(query.data, 'uz')

    user_id = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name or user_id
    set_user_lang(user_id, username, lang)

    await query.edit_message_text(t(lang, 'language_set'))

    # Update command menu to match user's chosen language
    from main import set_user_commands
    await set_user_commands(context.bot, int(user_id), lang)

    # Returning user (already has a name) — go straight to main keyboard
    if get_display_name(user_id):
        # Still credit referral for returning users who haven't been referred before
        referrer_id = context.user_data.pop('referrer_id', None)
        if referrer_id:
            new_count = add_referral(referrer_id, user_id)
            if new_count > 0:
                lang_r = get_user_lang(referrer_id)
                try:
                    await context.bot.send_message(
                        chat_id=int(referrer_id),
                        text=t(lang_r, 'referral_joined', name=html.escape(username)),
                        parse_mode='HTML',
                    )
                except Exception:
                    pass
        in_group = query.message.chat.type in ('group', 'supergroup')
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=t(lang, 'welcome'),
            reply_markup=default_kb(lang, in_group),
        )
        return ConversationHandler.END

    # New user — ask for name, keep keyboard hidden
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=t(lang, 'onboard_enter_name'),
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data['onboard_lang'] = lang
    return NAME


async def name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = _uid(update)
    username = _uname(update)
    lang = context.user_data.get('onboard_lang') or get_user_lang(user_id)

    name = update.message.text.strip()[:50]
    if not name:
        await update.message.reply_text(t(lang, 'register_empty'))
        return NAME   # stay in this state

    set_display_name(user_id, username, name)
    logger.info("Onboarding complete: %s → %s", user_id, name)

    # Credit referrer if this user was invited
    referrer_id = context.user_data.pop('referrer_id', None)
    if referrer_id:
        new_count = add_referral(referrer_id, user_id)
        if new_count > 0:
            lang_r = get_user_lang(referrer_id)
            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=t(lang_r, 'referral_joined', name=html.escape(name)),
                    parse_mode='HTML',
                )
            except Exception:
                pass  # referrer may have blocked the bot

    in_group = update.effective_chat.type in ('group', 'supergroup')
    await update.message.reply_text(
        t(lang, 'onboard_done', name=html.escape(name)),
        parse_mode='HTML',
        reply_markup=default_kb(lang, in_group),
    )
    context.user_data.pop('onboard_lang', None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop('onboard_lang', None)
    return ConversationHandler.END


def build_onboarding_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANG: [CallbackQueryHandler(lang_selected, pattern=r'^onboard_')],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_entered)],
        },
        fallbacks=[CommandHandler('start', start)],
        per_user=True,
        per_chat=False,
        name='onboarding',
    )
