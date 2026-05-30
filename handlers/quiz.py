"""
Group quiz games:
  /quiz1  — 20 questions, 4-choice inline keyboard (A/B/C/D), 20 sec each
  /quiz2  — 20 questions, free-text, first correct answer wins, 15 sec each
"""
import html
import logging
import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from data import COUNTRIES, COUNTRIES_CAPITALS, COUNTRY_FLAGS, COUNTRY_HINTS_UZ
from database import get_user_lang
from keyboards import default_kb
from translations import t, get_country_name, get_hint

logger = logging.getLogger(__name__)

QUIZ_SIZE      = 20
VARIANT_SECS   = 20   # seconds per variant question
TEXT_SECS      = 15   # seconds per text question

# chat_id → state
active_variant_quizzes: dict = {}
active_text_quizzes:    dict = {}

_LABELS = ['🅰', '🅱', '🅲', '🅳']


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _uid(u: Update) -> str:   return str(u.effective_user.id)
def _chat(u: Update) -> str:  return str(u.effective_chat.id)
def _uname(u: Update) -> str:
    x = u.effective_user
    return x.username or x.first_name or str(x.id)


def _make_choices(correct_uz: str, n: int = 4) -> tuple[list[str], int]:
    """(capital_list, correct_index)  for a variant question."""
    pool = [c for c in COUNTRIES if c != correct_uz and COUNTRIES_CAPITALS.get(c)]
    decoys = random.sample(pool, min(n - 1, len(pool)))
    bucket = decoys + [correct_uz]
    random.shuffle(bucket)
    idx = bucket.index(correct_uz)
    return [COUNTRIES_CAPITALS[c] for c in bucket], idx


def _scoreboard(scores: dict) -> str:
    if not scores:
        return "—"
    medals = ['🥇', '🥈', '🥉']
    rows = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    lines = []
    for i, (_, d) in enumerate(rows[:10]):
        med = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{med} <b>{html.escape(d['name'])}</b> — {d['score']}")
    return '\n'.join(lines)


def _quiz_i18n(lang: str, key: str, **kw) -> str:
    strings = {
        'uz': {
            'variant_start':  "🎮 <b>Viktorina boshlanadi!</b>\n20 ta savol · Har biriga 20 soniya\nVariantlardan birini tanlang 👇",
            'text_start':     "🎮 <b>Viktorina boshlanadi!</b>\n20 ta savol · Har biriga 15 soniya\nJavobni yozing, birinchi to'g'ri javob ball oladi!",
            'q_variant':      "❓ <b>{idx}/{total}</b>\n\n{flag} <b>{country}</b>\n\n🏙 Poytaxti qaysi shahar?",
            'q_text':         "❓ <b>{idx}/{total}</b>\n\n🏙 <b>{capital}</b> {flag}\n\nBu qaysi davlat?",
            'correct_ans':    "✅ {label} <b>{capital}</b>",
            'first_correct':  "✅ <b>{name}</b> +1 · {flag} <b>{country}</b>",
            'timeout':        "⏰ {flag} <b>{country}</b>",
            'results':        "🏆 <b>Viktorina tugadi!</b>\n\n{board}",
            'no_scores':      "Hech kim to'g'ri javob bermadi.",
            'already':        "⚠️ Allaqachon quiz bor!",
            'stopped':        "✅ Quiz to'xtatildi.",
            'none':           "Faol quiz yo'q.",
        },
        'ru': {
            'variant_start':  "🎮 <b>Квиз начинается!</b>\n20 вопросов · 20 секунд на каждый\nВыберите один из вариантов 👇",
            'text_start':     "🎮 <b>Квиз начинается!</b>\n20 вопросов · 15 секунд на каждый\nПишите ответ, первый правильный получает балл!",
            'q_variant':      "❓ <b>{idx}/{total}</b>\n\n{flag} <b>{country}</b>\n\n🏙 Какова столица?",
            'q_text':         "❓ <b>{idx}/{total}</b>\n\n🏙 <b>{capital}</b> {flag}\n\nЧья это столица?",
            'correct_ans':    "✅ {label} <b>{capital}</b>",
            'first_correct':  "✅ <b>{name}</b> +1 · {flag} <b>{country}</b>",
            'timeout':        "⏰ {flag} <b>{country}</b>",
            'results':        "🏆 <b>Квиз завершён!</b>\n\n{board}",
            'no_scores':      "Никто не ответил правильно.",
            'already':        "⚠️ Квиз уже идёт!",
            'stopped':        "✅ Квиз остановлен.",
            'none':           "Нет активного квиза.",
        },
        'en': {
            'variant_start':  "🎮 <b>Quiz starts!</b>\n20 questions · 20 seconds each\nPick one of the options 👇",
            'text_start':     "🎮 <b>Quiz starts!</b>\n20 questions · 15 seconds each\nType your answer — first correct wins a point!",
            'q_variant':      "❓ <b>{idx}/{total}</b>\n\n{flag} <b>{country}</b>\n\n🏙 What is the capital?",
            'q_text':         "❓ <b>{idx}/{total}</b>\n\n🏙 <b>{capital}</b> {flag}\n\nWhich country?",
            'correct_ans':    "✅ {label} <b>{capital}</b>",
            'first_correct':  "✅ <b>{name}</b> +1 · {flag} <b>{country}</b>",
            'timeout':        "⏰ {flag} <b>{country}</b>",
            'results':        "🏆 <b>Quiz finished!</b>\n\n{board}",
            'no_scores':      "Nobody answered correctly.",
            'already':        "⚠️ A quiz is already running!",
            'stopped':        "✅ Quiz stopped.",
            'none':           "No active quiz.",
        },
    }
    tmpl = strings.get(lang, strings['en']).get(key, key)
    return tmpl.format(**kw) if kw else tmpl


# ──────────────────────────────────────────────────────────────────────────────
#  TYPE 1 — VARIANT (inline keyboard A/B/C/D)
# ──────────────────────────────────────────────────────────────────────────────

async def start_variant_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat(update)
    lang = get_user_lang(_uid(update))

    if chat_id in active_variant_quizzes or chat_id in active_text_quizzes:
        await update.message.reply_text(_quiz_i18n(lang, 'already'))
        return

    questions = random.sample(COUNTRIES, QUIZ_SIZE)
    active_variant_quizzes[chat_id] = {
        'questions': questions, 'current': 0,
        'scores': {}, 'answered': set(),
        'correct_idx': 0, 'correct_uz': '',
        'job': None, 'lang': lang, 'msg_id': None,
    }
    await update.message.reply_text(_quiz_i18n(lang, 'variant_start'), parse_mode='HTML')
    await _send_variant_q(context, chat_id)


async def _send_variant_q(context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> None:
    quiz = active_variant_quizzes.get(chat_id)
    if not quiz:
        return

    idx    = quiz['current']
    lang   = quiz['lang']
    cuz    = quiz['questions'][idx]
    choices, correct_idx = _make_choices(cuz)

    quiz.update(correct_idx=correct_idx, correct_uz=cuz, answered=set())

    country_display = get_country_name(cuz, lang)
    flag = COUNTRY_FLAGS.get(cuz, '🌍')

    text = _quiz_i18n(lang, 'q_variant',
                      idx=idx + 1, total=QUIZ_SIZE,
                      flag=flag, country=html.escape(country_display))
    text += '\n\n' + '\n'.join(
        f"{_LABELS[i]} {html.escape(c)}" for i, c in enumerate(choices)
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{_LABELS[i]} {c[:28]}", callback_data=f"vq:{chat_id}:{i}")
         for i, c in enumerate(choices[:2])],
        [InlineKeyboardButton(f"{_LABELS[i]} {c[:28]}", callback_data=f"vq:{chat_id}:{i}")
         for i, c in enumerate(choices[2:], 2)],
    ])

    msg = await context.bot.send_message(
        chat_id=int(chat_id), text=text, parse_mode='HTML', reply_markup=kb
    )
    quiz['msg_id'] = msg.message_id

    if quiz.get('job'):
        quiz['job'].schedule_removal()
    quiz['job'] = context.application.job_queue.run_once(
        _variant_timeout,
        VARIANT_SECS,
        data={'chat_id': chat_id},
        name=f"vquiz_{chat_id}",
    )


async def handle_variant_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    parts = query.data.split(':')   # vq:chat_id:answer_idx
    if len(parts) != 3:
        await query.answer(); return

    chat_id = parts[1]
    try:
        answer_idx = int(parts[2])
    except ValueError:
        await query.answer(); return

    quiz = active_variant_quizzes.get(chat_id)
    if not quiz:
        await query.answer("Quiz ended!"); return

    user_id  = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name or user_id

    if user_id in quiz['answered']:
        await query.answer("⏳ Already answered!"); return

    quiz['answered'].add(user_id)
    if answer_idx == quiz['correct_idx']:
        quiz['scores'].setdefault(user_id, {'name': username, 'score': 0})
        quiz['scores'][user_id]['score'] += 1
        await query.answer("✅ Correct! +1")
    else:
        await query.answer("❌ Wrong!")


async def _variant_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    quiz = active_variant_quizzes.get(chat_id)
    if not quiz:
        return

    lang    = quiz['lang']
    cuz     = quiz['correct_uz']
    cap     = COUNTRIES_CAPITALS.get(cuz, '?')
    label   = _LABELS[quiz['correct_idx']]

    # Remove inline keyboard from question message
    if quiz.get('msg_id'):
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=int(chat_id), message_id=quiz['msg_id'], reply_markup=None
            )
        except Exception:
            pass

    await context.bot.send_message(
        chat_id=int(chat_id),
        text=_quiz_i18n(lang, 'correct_ans', label=label, capital=html.escape(cap)),
        parse_mode='HTML',
    )

    quiz['current'] += 1
    if quiz['current'] >= QUIZ_SIZE:
        await _finish(context, chat_id, 'variant')
    else:
        await _send_variant_q(context, chat_id)


# ──────────────────────────────────────────────────────────────────────────────
#  TYPE 2 — TEXT (free-text, first correct wins)
# ──────────────────────────────────────────────────────────────────────────────

async def start_text_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat(update)
    lang = get_user_lang(_uid(update))

    if chat_id in active_variant_quizzes or chat_id in active_text_quizzes:
        await update.message.reply_text(_quiz_i18n(lang, 'already'))
        return

    questions = random.sample(COUNTRIES, QUIZ_SIZE)
    active_text_quizzes[chat_id] = {
        'questions': questions, 'current': 0,
        'scores': {}, 'answered': False,
        'correct_uz': '', 'job': None, 'lang': lang,
    }
    await update.message.reply_text(_quiz_i18n(lang, 'text_start'), parse_mode='HTML')
    await _send_text_q(context, chat_id)


async def _send_text_q(context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> None:
    quiz = active_text_quizzes.get(chat_id)
    if not quiz:
        return

    idx  = quiz['current']
    lang = quiz['lang']
    cuz  = quiz['questions'][idx]
    cap  = COUNTRIES_CAPITALS.get(cuz, '?')
    flag = COUNTRY_FLAGS.get(cuz, '🌍')

    quiz.update(correct_uz=cuz, answered=False)

    text = _quiz_i18n(lang, 'q_text',
                      idx=idx + 1, total=QUIZ_SIZE,
                      capital=html.escape(cap), flag=flag)

    await context.bot.send_message(chat_id=int(chat_id), text=text, parse_mode='HTML')

    if quiz.get('job'):
        quiz['job'].schedule_removal()
    quiz['job'] = context.application.job_queue.run_once(
        _text_timeout,
        TEXT_SECS,
        data={'chat_id': chat_id},
        name=f"tquiz_{chat_id}",
    )


async def check_text_quiz_answer(
    chat_id: str, user_id: str, username: str,
    guess_uz: str, update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Called from handle_guess. Returns True if the message was consumed."""
    quiz = active_text_quizzes.get(chat_id)
    if not quiz or quiz['answered']:
        return False
    if guess_uz.lower() != quiz['correct_uz'].lower():
        return False   # wrong — keep silent, let others try

    quiz['answered'] = True
    if quiz.get('job'):
        quiz['job'].schedule_removal()

    quiz['scores'].setdefault(user_id, {'name': username, 'score': 0})
    quiz['scores'][user_id]['score'] += 1

    lang = quiz['lang']
    cuz  = quiz['correct_uz']
    flag = COUNTRY_FLAGS.get(cuz, '🌍')
    name = update.effective_user.first_name or username

    await update.message.reply_text(
        _quiz_i18n(lang, 'first_correct',
                   name=html.escape(name),
                   flag=flag,
                   country=html.escape(get_country_name(cuz, lang))),
        parse_mode='HTML',
    )

    quiz['current'] += 1
    if quiz['current'] >= QUIZ_SIZE:
        await _finish(context, chat_id, 'text')
    else:
        quiz['job'] = context.application.job_queue.run_once(
            _next_text_q_job,
            3,
            data={'chat_id': chat_id},
            name=f"tquiz_next_{chat_id}",
        )
    return True


async def _next_text_q_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_text_q(context, context.job.data['chat_id'])


async def _text_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    quiz = active_text_quizzes.get(chat_id)
    if not quiz:
        return

    lang = quiz['lang']
    cuz  = quiz['correct_uz']
    flag = COUNTRY_FLAGS.get(cuz, '🌍')

    await context.bot.send_message(
        chat_id=int(chat_id),
        text=_quiz_i18n(lang, 'timeout',
                        flag=flag,
                        country=html.escape(get_country_name(cuz, lang))),
        parse_mode='HTML',
    )

    quiz['current'] += 1
    if quiz['current'] >= QUIZ_SIZE:
        await _finish(context, chat_id, 'text')
    else:
        await _send_text_q(context, chat_id)


# ──────────────────────────────────────────────────────────────────────────────
#  FINISH & STOP
# ──────────────────────────────────────────────────────────────────────────────

async def _finish(context: ContextTypes.DEFAULT_TYPE, chat_id: str, qtype: str) -> None:
    if qtype == 'variant':
        quiz = active_variant_quizzes.pop(chat_id, None)
    else:
        quiz = active_text_quizzes.pop(chat_id, None)
    if not quiz:
        return

    lang   = quiz.get('lang', 'uz')
    scores = quiz.get('scores', {})
    board  = _scoreboard(scores) if scores else _quiz_i18n(lang, 'no_scores')

    await context.bot.send_message(
        chat_id=int(chat_id),
        text=_quiz_i18n(lang, 'results', board=board),
        parse_mode='HTML',
    )


async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat(update)
    lang = get_user_lang(_uid(update))
    stopped = False
    for d in (active_variant_quizzes, active_text_quizzes):
        q = d.pop(chat_id, None)
        if q:
            if q.get('job'):
                q['job'].schedule_removal()
            stopped = True
    msg = _quiz_i18n(lang, 'stopped') if stopped else _quiz_i18n(lang, 'none')
    await update.message.reply_text(msg)
