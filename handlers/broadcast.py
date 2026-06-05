"""
Admin broadcast — supports text, photos, videos, albums (media groups).
/broadcast → admin sends any message → forwarded to all users.
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

_KEY = 'awaiting_broadcast'
# buffer for collecting album photos: group_id -> {from_chat, msg_ids, uid}
_ALBUMS: dict = {}


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
        "Xabar, rasm, video, albom — istalgan kontent yuboring.\n"
        "Bekor qilish: /cancel",
        parse_mode='HTML',
    )


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(_KEY, None)
    await update.message.reply_text("❌ Broadcast bekor qilindi.")


async def _do_broadcast(context: ContextTypes.DEFAULT_TYPE,
                        from_chat: int, msg_ids: list[int],
                        admin_uid: str, reply_to_msg) -> None:
    """Forward one or more messages to all users."""
    try:
        from database import _get_conn, _exec
        with _get_conn() as conn:
            rows = _exec(conn, 'SELECT user_id FROM users').fetchall()
        user_ids = [r[0] for r in rows if not str(r[0]).startswith('-')]
        total = len(user_ids)
    except Exception as e:
        logger.error("Broadcast DB error: %s", e)
        try:
            await reply_to_msg.reply_text(f"❌ DB xatosi: {e}")
        except Exception:
            pass
        return

    logger.info("Broadcast: admin=%s msgs=%d users=%d", admin_uid, len(msg_ids), total)

    status = await reply_to_msg.reply_text(
        f"📢 Broadcast boshlandi · 👥 {total}\n⏳ Jo'natilmoqda..."
    )

    sent = failed = 0
    for i, uid in enumerate(user_ids):
        try:
            if len(msg_ids) == 1:
                await context.bot.forward_message(
                    chat_id=int(uid), from_chat_id=from_chat, message_id=msg_ids[0]
                )
            else:
                # Forward album (multiple messages)
                await context.bot.forward_messages(
                    chat_id=int(uid), from_chat_id=from_chat, message_ids=msg_ids
                )
            sent += 1
        except Exception as e:
            failed += 1
            logger.debug("Broadcast skip %s: %s", uid, str(e)[:60])

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
            f"❌ Bloklagan: <b>{failed}</b>\n"
            f"👥 Jami: <b>{total}</b>",
            parse_mode='HTML',
        )
    except Exception:
        pass
    logger.info("Broadcast done: sent=%d failed=%d total=%d", sent, failed, total)


async def _album_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job fires 1s after first photo — by then all album photos have arrived."""
    data = context.job.data
    group_id = data['group_id']
    info = _ALBUMS.pop(group_id, None)
    if not info:
        return
    await _do_broadcast(
        context,
        from_chat=info['from_chat'],
        msg_ids=info['msg_ids'],
        admin_uid=info['uid'],
        reply_to_msg=info['reply_msg'],
    )


async def broadcast_handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if message consumed as broadcast."""
    uid = str(update.effective_user.id)
    if not context.user_data.get(_KEY):
        return False
    if not _is_admin(uid):
        context.user_data.pop(_KEY, None)
        return False

    msg = update.message
    from_chat = update.effective_chat.id
    group_id = msg.media_group_id if msg else None

    if group_id:
        # Album: collect all photos, fire job after 1s
        if group_id not in _ALBUMS:
            _ALBUMS[group_id] = {
                'from_chat': from_chat,
                'msg_ids': [],
                'uid': uid,
                'reply_msg': msg,
            }
            # Clear flag now so subsequent album photos don't re-trigger
            context.user_data.pop(_KEY, None)
        _ALBUMS[group_id]['msg_ids'].append(msg.message_id)

        # Reset 1s countdown (cancel old job, schedule new)
        job_name = f"bc_album_{group_id}"
        for j in context.application.job_queue.get_jobs_by_name(job_name):
            j.schedule_removal()
        context.application.job_queue.run_once(
            _album_job, 1.0,
            data={'group_id': group_id},
            name=job_name,
        )
        return True
    else:
        # Single message: broadcast immediately
        context.user_data.pop(_KEY, None)
        await _do_broadcast(context, from_chat, [msg.message_id], uid, msg)
        return True
