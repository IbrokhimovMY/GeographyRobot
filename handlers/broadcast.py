"""Admin broadcast: send a message to all registered users."""
import asyncio
import html
import logging

from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters,
)

from config import ADMIN_IDS
from database import get_user_lang
from keyboards import default_kb

logger = logging.getLogger(__name__)

WAITING_MESSAGE = 1


def _is_admin(update: Update) -> bool:
    uid = str(update.effective_user.id)
    return uid in ADMIN_IDS


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_admin(update):
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 <b>Broadcast</b>\n\n"
        "Xabar matnini yozing (HTML format qo'llab-quvvatlanadi).\n"
        "Bekor qilish uchun /cancel",
        parse_mode='HTML',
    )
    return WAITING_MESSAGE


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not _is_admin(update):
        return ConversationHandler.END

    msg_text = update.message.text or update.message.caption or ''
    if not msg_text:
        await update.message.reply_text("❌ Matn bo'sh.")
        return WAITING_MESSAGE

    # Get all user IDs from DB
    from database import _get_conn, _exec
    with _get_conn() as conn:
        rows = _exec(conn,
            "SELECT user_id FROM users WHERE user_id NOT LIKE '-%'"
        ).fetchall()

    user_ids = [r[0] for r in rows]
    total = len(user_ids)

    status = await update.message.reply_text(
        f"⏳ Jo'natilmoqda... (0/{total})"
    )

    sent = 0
    failed = 0
    logger.info("Broadcast started: total=%d", total)
    for i, uid in enumerate(user_ids):
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=msg_text,
                parse_mode='HTML',
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.debug("Broadcast skip uid=%s: %s", uid, e)

        # Update progress every 5 users (or last user)
        if (i + 1) % 5 == 0 or (i + 1) == total:
            try:
                await status.edit_text(
                    f"⏳ Jo'natilmoqda... ({i+1}/{total}) ✅{sent} ❌{failed}"
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)  # ~20 msg/sec — Telegram limit

    await status.edit_text(
        f"✅ <b>Broadcast tugadi</b>\n\n"
        f"📨 Jo'natildi: <b>{sent}</b>\n"
        f"❌ Xato: <b>{failed}</b>\n"
        f"👥 Jami: <b>{total}</b>",
        parse_mode='HTML',
    )
    logger.info("Broadcast: sent=%d failed=%d total=%d", sent, failed, total)
    return ConversationHandler.END


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END


def build_broadcast_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_start)],
        states={
            WAITING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send),
            ],
        },
        fallbacks=[CommandHandler('cancel', broadcast_cancel)],
        per_user=True, per_chat=False, name='broadcast',
    )
