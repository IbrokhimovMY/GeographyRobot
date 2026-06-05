"""
Admin broadcast — no conversation state needed.
Usage: /broadcast Your message text here
       /broadcast <b>HTML</b> supported too
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import ADMIN_IDS

logger = logging.getLogger(__name__)


def _is_admin(update: Update) -> bool:
    return str(update.effective_user.id) in ADMIN_IDS


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update):
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return

    # Message text comes after /broadcast command
    msg_text = ' '.join(context.args) if context.args else ''
    if not msg_text:
        await update.message.reply_text(
            "📢 <b>Broadcast</b>\n\n"
            "Ishlatish: <code>/broadcast Xabar matni</code>\n\n"
            "Misol:\n<code>/broadcast Yangi funksiya qo'shildi!</code>",
            parse_mode='HTML',
        )
        return

    logger.info("Broadcast started by admin=%s: '%s...'",
                update.effective_user.id, msg_text[:40])

    # Get all user IDs
    try:
        from database import _get_conn, _exec
        with _get_conn() as conn:
            rows = _exec(conn, 'SELECT user_id FROM users').fetchall()
        user_ids = [r[0] for r in rows if not str(r[0]).startswith('-')]
        total = len(user_ids)
    except Exception as e:
        logger.error("Broadcast DB error: %s", e)
        await update.message.reply_text(f"❌ DB xatosi: {e}")
        return

    status = await update.message.reply_text(
        f"📢 Broadcast boshlandi\n"
        f"👥 Foydalanuvchilar: {total}\n"
        f"⏳ Jo'natilmoqda..."
    )

    sent = failed = 0
    for i, uid in enumerate(user_ids):
        try:
            await context.bot.send_message(
                chat_id=int(uid), text=msg_text, parse_mode='HTML'
            )
            sent += 1
        except Exception as e:
            err = str(e)
            if 'parse' in err.lower() or 'entity' in err.lower():
                try:
                    await context.bot.send_message(chat_id=int(uid), text=msg_text)
                    sent += 1
                except Exception:
                    failed += 1
            else:
                failed += 1
            logger.info("Broadcast skip uid=%s: %s", uid, err[:60])

        if (i + 1) % 10 == 0 or (i + 1) == total:
            try:
                await status.edit_text(
                    f"⏳ Jo'natilmoqda... ({i+1}/{total}) ✅{sent} ❌{failed}"
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)

    try:
        await status.edit_text(
            f"✅ <b>Broadcast tugadi</b>\n\n"
            f"📨 Jo'natildi: <b>{sent}</b>\n"
            f"❌ Xato: <b>{failed}</b>\n"
            f"👥 Jami: <b>{total}</b>",
            parse_mode='HTML',
        )
    except Exception:
        await update.message.reply_text(
            f"✅ Broadcast tugadi: {sent}/{total} jo'natildi"
        )

    logger.info("Broadcast done: sent=%d failed=%d total=%d", sent, failed, total)


def build_broadcast_handler():
    return CommandHandler('broadcast', broadcast_command)
