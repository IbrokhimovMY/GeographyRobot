"""
Admin broadcast — bot nomidan yuboradi (forward emas).
/broadcast → admin xabar/rasm/albom yuboradi → bot foydalanuvchilarga copy qiladi.
"""
import asyncio
import logging

from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

_KEY = 'awaiting_broadcast'
# album buffer: group_id -> {'msgs': [Message, ...], 'uid': str}
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
        "Xabar, rasm, video yoki albom yuboring.\n"
        "Bekor qilish: /cancel",
        parse_mode='HTML',
    )


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(_KEY, None)
    await update.message.reply_text("❌ Broadcast bekor qilindi.")


async def _send_to_user(context: ContextTypes.DEFAULT_TYPE,
                        uid: int, messages: list) -> bool:
    """Send one or more messages to a single user as bot's own messages."""
    try:
        if len(messages) == 1:
            msg = messages[0]
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
            )
        else:
            # Album — build InputMedia list
            media = []
            for msg in messages:
                caption = msg.caption or None
                if msg.photo:
                    file_id = msg.photo[-1].file_id
                    media.append(InputMediaPhoto(media=file_id, caption=caption))
                elif msg.video:
                    file_id = msg.video.file_id
                    media.append(InputMediaVideo(media=file_id, caption=caption))
            if media:
                await context.bot.send_media_group(chat_id=uid, media=media)
            else:
                # fallback: copy each
                for msg in messages:
                    await context.bot.copy_message(
                        chat_id=uid,
                        from_chat_id=msg.chat_id,
                        message_id=msg.message_id,
                    )
        return True
    except Exception:
        return False


async def _do_broadcast(context: ContextTypes.DEFAULT_TYPE,
                        messages: list, admin_uid: str,
                        reply_msg) -> None:
    try:
        from database import _get_conn, _exec
        with _get_conn() as conn:
            rows = _exec(conn, 'SELECT user_id FROM users').fetchall()
        user_ids = [r[0] for r in rows if not str(r[0]).startswith('-')]
        total = len(user_ids)
    except Exception as e:
        logger.error("Broadcast DB error: %s", e)
        await reply_msg.reply_text(f"❌ DB xatosi: {e}")
        return

    logger.info("Broadcast: admin=%s msgs=%d users=%d", admin_uid, len(messages), total)
    status = await reply_msg.reply_text(
        f"📢 {total} foydalanuvchiga jo'natilmoqda..."
    )

    sent = failed = 0
    for i, uid in enumerate(user_ids):
        ok = await _send_to_user(context, int(uid), messages)
        if ok:
            sent += 1
        else:
            failed += 1

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
    data = context.job.data
    group_id = data['group_id']
    info = _ALBUMS.pop(group_id, None)
    if not info:
        return
    await _do_broadcast(context, info['msgs'], info['uid'], info['reply_msg'])


async def broadcast_handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = str(update.effective_user.id)
    msg = update.message
    if not msg:
        return False

    group_id = msg.media_group_id

    # Album continuation — add to existing buffer regardless of _KEY
    if group_id and group_id in _ALBUMS:
        _ALBUMS[group_id]['msgs'].append(msg)
        job_name = f"bc_album_{group_id}"
        for j in context.application.job_queue.get_jobs_by_name(job_name):
            j.schedule_removal()
        context.application.job_queue.run_once(
            _album_job, 1.0, data={'group_id': group_id}, name=job_name,
        )
        return True

    if not context.user_data.get(_KEY):
        return False
    if not _is_admin(uid):
        context.user_data.pop(_KEY, None)
        return False

    context.user_data.pop(_KEY, None)

    if group_id:
        # First photo of a new album
        _ALBUMS[group_id] = {'msgs': [msg], 'uid': uid, 'reply_msg': msg}
        job_name = f"bc_album_{group_id}"
        context.application.job_queue.run_once(
            _album_job, 1.0, data={'group_id': group_id}, name=job_name,
        )
    else:
        # Single message
        await _do_broadcast(context, [msg], uid, msg)
    return True
