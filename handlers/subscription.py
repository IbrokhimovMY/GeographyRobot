"""Mandatory channel subscription middleware."""
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ApplicationHandlerStop

from config import REQUIRED_CHANNEL, ADMIN_IDS
from database import get_user_lang

logger = logging.getLogger(__name__)

_MSG = {
    'uz': "📢 Botdan foydalanish uchun kanalimizga obuna bo'ling!\n\nObuna bo'lgach, \"✅ Tekshirish\" tugmasini bosing.",
    'ru': "📢 Для использования бота подпишитесь на наш канал!\n\nПосле подписки нажмите кнопку \"✅ Проверить\".",
    'en': "📢 Please subscribe to our channel to use the bot!\n\nAfter subscribing, press \"✅ Check\" button.",
}
_BTN_JOIN = {'uz': "📢 Kanalga o'tish", 'ru': "📢 Перейти в канал", 'en': "📢 Join Channel"}
_BTN_CHECK = {'uz': "✅ Tekshirish", 'ru': "✅ Проверить", 'en': "✅ Check"}
_OK = {'uz': "✅ Rahmat! Endi botdan foydalanishingiz mumkin.", 'ru': "✅ Спасибо! Теперь можете пользоваться ботом.", 'en': "✅ Thank you! You can now use the bot."}
_FAIL = {'uz': "❌ Siz hali obuna bo'lmagansiz. Iltimos, avval kanalga obuna bo'ling.", 'ru': "❌ Вы ещё не подписаны. Пожалуйста, сначала подпишитесь.", 'en': "❌ You haven't subscribed yet. Please subscribe to the channel first."}


async def _is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status not in ('left', 'kicked')
    except Exception as e:
        logger.debug("subscription check failed uid=%s: %s", user_id, e)
        return True  # if check fails, let through


def _sub_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(_BTN_JOIN.get(lang, _BTN_JOIN['en']), url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}"),
        InlineKeyboardButton(_BTN_CHECK.get(lang, _BTN_CHECK['en']), callback_data="sub_check"),
    ]])


async def subscription_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not REQUIRED_CHANNEL:
        return

    user = update.effective_user
    if not user:
        return

    # Admins bypass the check
    if str(user.id) in ADMIN_IDS:
        return

    # Handle "✅ Tekshirish" button press
    if update.callback_query and update.callback_query.data == 'sub_check':
        lang = get_user_lang(str(user.id))
        if await _is_subscribed(context.bot, user.id):
            await update.callback_query.answer(_OK.get(lang, _OK['en']), show_alert=True)
            try:
                await update.callback_query.message.delete()
            except Exception:
                pass
        else:
            await update.callback_query.answer(_FAIL.get(lang, _FAIL['en']), show_alert=True)
        raise ApplicationHandlerStop

    if await _is_subscribed(context.bot, user.id):
        return

    lang = get_user_lang(str(user.id))
    chat_id = update.effective_chat.id if update.effective_chat else user.id
    await context.bot.send_message(
        chat_id=chat_id,
        text=_MSG.get(lang, _MSG['en']),
        reply_markup=_sub_kb(lang),
    )
    raise ApplicationHandlerStop
