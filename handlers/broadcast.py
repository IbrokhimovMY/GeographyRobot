"""
Admin broadcast — forwards any message type to all users.
/broadcast → admin sends any message → forwarded to all users.
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

_KEY = 'awaiting_broadcast'


def _is_admin(uid: str) -> bool:
    return uid in ADMIN_IDS


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = str(update.effective_user.id)
    if not _is_admin(uid):
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return
    context.user_data[_KEY] = True
    await update.message.reply_text(
        "📢 <b>Broadcast</b>\n\n"
        "Xabar, rasm, video yoki istalgan kontent yuboring.\n"
        "Bekor qilish: /cancel",
        parse_mode='HTML',
    )


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(_KEY, None)
    await update.message.reply_text("❌ Broadcast bekor qilindi.")


async def broadcast_handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Called from handle_guess and media handler. Returns True if consumed."""
    uid = str(update.effective_user.id)
    if not context.user_data.get(_KEY):
        return False
    if not _is_admin(uid):
        context.user_data.pop(_KEY, None)
        return False

    context.user_data.pop(_KEY, None)

    try:
        from database import _get_conn, _exec
        with _get_conn() as conn:
            rows = _exec(conn, 'SELECT user_id FROM users').fetchall()
        user_ids = [r[0] for r in rows if not str(r[0]).startswith('-')]
        total = len(user_ids)
    except Exception as e:
        logger.error("Broadcast DB error: %s", e)
        await update.message.reply_text(f"❌ DB xatosi: {e}")
        return True

    logger.info("Broadcast: admin=%s total=%d", uid, total)
    status = await update.message.reply_text(
        f"📢 Broadcast boshlandi · 👥 {total} foydalanuvchi\n⏳ Jo'natilmoqda..."
    )

    from_chat = update.effective_chat.id
    msg_id = update.message.message_id

    sent = failed = 0
    for i, to_uid in enumerate(user_ids):
        try:
            await context.bot.forward_message(
                chat_id=int(to_uid),
                from_chat_id=from_chat,
                message_id=msg_id,
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.debug("Broadcast skip %s: %s", to_uid, str(e)[:50])

        if (i + 1) % 10 == 0 or (i + 1) == total:
            try:
                await status.edit_text(f"⏳ {i+1}/{total} · ✅{sent} ❌{failed}")
            except Exception:
                pass

        await asyncio.sleep(0.05)

    try:
        await status.edit_text(
            f"✅ <b>Broadcast tugadi</b>\n\n"
            f"📨 Jo'natildi: <b>{sent}</b>\n"
            f"❌ Xato (bloklagan): <b>{failed}</b>\n"
            f"👥 Jami: <b>{total}</b>",
            parse_mode='HTML',
        )
    except Exception:
        pass

    logger.info("Broadcast done: sent=%d failed=%d total=%d", sent, failed, total)
    return True
