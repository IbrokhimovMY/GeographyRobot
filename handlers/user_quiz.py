"""
User-created quiz questions:
  /addquestion  — step-by-step wizard to add a question
  /myquestions  — list and delete your questions
"""
import html
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)

from database import (
    get_user_lang, get_display_name, add_user_question,
    get_user_questions, delete_user_question, count_user_questions,
)
from keyboards import default_kb

logger = logging.getLogger(__name__)

# Conversation states
Q_TEXT, Q_A, Q_B, Q_C, Q_D, Q_CORRECT = range(6)

_LABELS = ['A', 'B', 'C', 'D']

_I18N = {
    'uz': {
        'start':   "📝 <b>Savol qo'shish</b>\n\nSavol matnini yozing:",
        'opt_a':   "✅ Savol qabul qilindi.\n\n<b>A)</b> variant:",
        'opt_b':   "<b>B)</b> variant:",
        'opt_c':   "<b>C)</b> variant:",
        'opt_d':   "<b>D)</b> variant:",
        'correct': "To'g'ri javob harfini tanlang:",
        'saved':   "✅ Savolingiz saqlandi! (ID: {id})\nJami sizning savollaringiz: {total}",
        'cancel':  "❌ Bekor qilindi.",
        'myq_hdr': "📋 <b>Sizning savollaringiz</b> ({total} ta):",
        'myq_empty': "Hali savol qo'shmagansiz.",
        'deleted': "🗑 Savol #{id} o'chirildi.",
        'no_q':    "Savol topilmadi.",
        'total':   "📊 Jami foydalanuvchi savollari: <b>{n}</b>",
    },
    'ru': {
        'start':   "📝 <b>Добавить вопрос</b>\n\nНапишите текст вопроса:",
        'opt_a':   "✅ Вопрос принят.\n\n<b>A)</b> вариант:",
        'opt_b':   "<b>B)</b> вариант:",
        'opt_c':   "<b>C)</b> вариант:",
        'opt_d':   "<b>D)</b> вариант:",
        'correct': "Выберите правильный ответ:",
        'saved':   "✅ Вопрос сохранён! (ID: {id})\nВсего ваших вопросов: {total}",
        'cancel':  "❌ Отменено.",
        'myq_hdr': "📋 <b>Ваши вопросы</b> ({total} шт.):",
        'myq_empty': "Вы ещё не добавляли вопросов.",
        'deleted': "🗑 Вопрос #{id} удалён.",
        'no_q':    "Вопрос не найден.",
        'total':   "📊 Всего вопросов пользователей: <b>{n}</b>",
    },
    'en': {
        'start':   "📝 <b>Add a question</b>\n\nWrite the question text:",
        'opt_a':   "✅ Question saved.\n\n<b>A)</b> option:",
        'opt_b':   "<b>B)</b> option:",
        'opt_c':   "<b>C)</b> option:",
        'opt_d':   "<b>D)</b> option:",
        'correct': "Select the correct answer:",
        'saved':   "✅ Question saved! (ID: {id})\nYour total questions: {total}",
        'cancel':  "❌ Cancelled.",
        'myq_hdr': "📋 <b>Your questions</b> ({total}):",
        'myq_empty': "You haven't added any questions yet.",
        'deleted': "🗑 Question #{id} deleted.",
        'no_q':    "Question not found.",
        'total':   "📊 Total user questions: <b>{n}</b>",
    },
}


def _t(lang: str, key: str, **kw) -> str:
    s = _I18N.get(lang, _I18N['en']).get(key, key)
    return s.format(**kw) if kw else s


def _uid(u: Update) -> str: return str(u.effective_user.id)
def _uname(u: Update) -> str:
    x = u.effective_user
    return x.username or x.first_name or str(x.id)
def _lang(u: Update) -> str: return get_user_lang(_uid(u))


def _correct_kb(lang: str, prefix: str = 'aq_correct') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"🅰 A", callback_data=f"{prefix}:0"),
        InlineKeyboardButton(f"🅱 B", callback_data=f"{prefix}:1"),
        InlineKeyboardButton(f"🅲 C", callback_data=f"{prefix}:2"),
        InlineKeyboardButton(f"🅳 D", callback_data=f"{prefix}:3"),
    ]])


# ─── Add question wizard ──────────────────────────────────────────────────────

async def addquestion_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(update)
    context.user_data['aq'] = {'lang': lang}
    in_group = update.effective_chat.type in ('group', 'supergroup')
    await update.message.reply_text(_t(lang, 'start'), parse_mode='HTML',
                                    reply_markup=default_kb(lang, in_group))
    return Q_TEXT


async def aq_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['aq']['lang']
    context.user_data['aq']['question'] = update.message.text.strip()
    await update.message.reply_text(_t(lang, 'opt_a'), parse_mode='HTML')
    return Q_A


async def aq_a(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['aq']['lang']
    context.user_data['aq']['opt_a'] = update.message.text.strip()
    await update.message.reply_text(_t(lang, 'opt_b'), parse_mode='HTML')
    return Q_B


async def aq_b(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['aq']['lang']
    context.user_data['aq']['opt_b'] = update.message.text.strip()
    await update.message.reply_text(_t(lang, 'opt_c'), parse_mode='HTML')
    return Q_C


async def aq_c(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['aq']['lang']
    context.user_data['aq']['opt_c'] = update.message.text.strip()
    await update.message.reply_text(_t(lang, 'opt_d'), parse_mode='HTML')
    return Q_D


async def aq_d(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['aq']['lang']
    context.user_data['aq']['opt_d'] = update.message.text.strip()
    await update.message.reply_text(
        _t(lang, 'correct'), parse_mode='HTML',
        reply_markup=_correct_kb(lang),
    )
    return Q_CORRECT


async def aq_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(':')
    correct_idx = int(parts[1])

    aq = context.user_data.get('aq', {})
    lang = aq.get('lang', 'uz')
    user_id = str(query.from_user.id)
    author_name = get_display_name(user_id) or query.from_user.first_name or user_id

    opts = [aq.get('opt_a', ''), aq.get('opt_b', ''),
            aq.get('opt_c', ''), aq.get('opt_d', '')]

    qid = add_user_question(
        author_id=user_id,
        author_name=author_name,
        question=aq.get('question', ''),
        opts=opts,
        correct=correct_idx,
        lang=lang,
    )
    total = len(get_user_questions(user_id))
    try:
        await query.edit_message_text(
            _t(lang, 'saved', id=qid, total=total), parse_mode='HTML'
        )
    except Exception:
        pass
    context.user_data.pop('aq', None)
    return ConversationHandler.END


async def aq_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(update)
    context.user_data.pop('aq', None)
    await update.message.reply_text(_t(lang, 'cancel'))
    return ConversationHandler.END


# ─── My questions ─────────────────────────────────────────────────────────────

async def myquestions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = _uid(update)
    lang = _lang(update)
    in_group = update.effective_chat.type in ('group', 'supergroup')
    qs = get_user_questions(user_id)

    if not qs:
        await update.message.reply_text(_t(lang, 'myq_empty'),
                                        reply_markup=default_kb(lang, in_group))
        return

    lines = [_t(lang, 'myq_hdr', total=len(qs))]
    for q in qs[:20]:
        correct_opt = q['opts'][q['correct']]
        lines.append(
            f"\n<b>#{q['id']}</b> {html.escape(q['question'][:60])}\n"
            f"  ✅ {html.escape(correct_opt[:40])}"
            f"  |  👁 {q['use_count']}"
        )

    # Delete buttons for first 10
    kb_rows = []
    for q in qs[:10]:
        kb_rows.append([InlineKeyboardButton(
            f"🗑 #{q['id']}",
            callback_data=f"aq_del:{q['id']}"
        )])

    await update.message.reply_text(
        '\n'.join(lines), parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(kb_rows) if kb_rows else None,
    )


async def myquestions_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    lang = get_user_lang(user_id)
    qid = int(query.data.split(':')[1])
    delete_user_question(qid, user_id)
    try:
        await query.edit_message_text(_t(lang, 'deleted', id=qid), parse_mode='HTML')
    except Exception:
        pass


# ─── ConversationHandler builder ─────────────────────────────────────────────

def build_addquestion_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('addquestion', addquestion_start)],
        states={
            Q_TEXT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, aq_text)],
            Q_A:       [MessageHandler(filters.TEXT & ~filters.COMMAND, aq_a)],
            Q_B:       [MessageHandler(filters.TEXT & ~filters.COMMAND, aq_b)],
            Q_C:       [MessageHandler(filters.TEXT & ~filters.COMMAND, aq_c)],
            Q_D:       [MessageHandler(filters.TEXT & ~filters.COMMAND, aq_d)],
            Q_CORRECT: [CallbackQueryHandler(aq_correct, pattern=r'^aq_correct:')],
        },
        fallbacks=[CommandHandler('cancel', aq_cancel)],
        per_user=True, per_chat=False, name='addquestion',
    )
