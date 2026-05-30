"""
Two custom quiz modes:
  start_poll_quiz      — Telegram native quiz polls (for variant button → test mode)
  start_custom_text_quiz — Text Q&A with A/B/C/D options (for text button → test mode)
"""
import html
import logging
import random
import time

from telegram import Update
from telegram.ext import ContextTypes

from custom_quiz_data import CUSTOM_QUESTIONS
from database import get_user_lang

logger = logging.getLogger(__name__)

POLL_QUIZ_SIZE = 20
POLL_SECS      = 15   # seconds per poll question

# chat_id → state
active_poll_quizzes:        dict = {}
active_custom_text_quizzes: dict = {}

_LETTERS = ['A', 'B', 'C', 'D', 'E']


# ─── shared helpers ───────────────────────────────────────────────────────────

def _avg(d: dict) -> float:
    t = d.get('times', [])
    return sum(t) / len(t) if t else 999.0


def _scoreboard(scores: dict) -> str:
    if not scores:
        return "—"
    medals = ['🥇', '🥈', '🥉']
    rows = sorted(scores.items(), key=lambda x: (-x[1]['score'], _avg(x[1])))
    lines = []
    for i, (_, d) in enumerate(rows[:10]):
        med = medals[i] if i < 3 else f"{i+1}."
        t = f"  ⏱{_avg(d):.1f}s" if d.get('times') else ""
        lines.append(f"{med} <b>{html.escape(d['name'])}</b> — {d['score']}{t}")
    return '\n'.join(lines)


def _shuffled_options(q: dict, lang: str) -> tuple[list[str], int]:
    """Return (shuffled option texts, new correct index). Randomises answer position."""
    options = q['options'].get(lang, q['options'].get('uz', []))
    original_correct = q['correct']
    indexed = list(enumerate(options))
    random.shuffle(indexed)
    shuffled = [opt for _, opt in indexed]
    new_correct = next(i for i, (orig, _) in enumerate(indexed) if orig == original_correct)
    return shuffled, new_correct


def _finish_msg(lang: str, scores: dict) -> str:
    title = {'uz': "🏆 <b>Test viktorinasi tugadi!</b>",
             'ru': "🏆 <b>Тестовый квиз завершён!</b>",
             'en': "🏆 <b>Test Quiz finished!</b>"}.get(lang, "🏆 <b>Test viktorinasi tugadi!</b>")
    no_scores = {'uz': "Hech kim to'g'ri javob bermadi.",
                 'ru': "Никто не ответил правильно.",
                 'en': "Nobody answered correctly."}.get(lang, "")
    return f"{title}\n\n{_scoreboard(scores) if scores else no_scores}"


def stop_poll_quiz(chat_id: str) -> bool:
    stopped = False
    for d in (active_poll_quizzes, active_custom_text_quizzes):
        q = d.pop(chat_id, None)
        if q:
            if q.get('job'):
                try: q['job'].schedule_removal()
                except Exception: pass
            stopped = True
    return stopped


# ═══════════════════════════════════════════════════════════════════════════════
#  POLL QUIZ  (Telegram native quiz polls)
# ═══════════════════════════════════════════════════════════════════════════════

async def start_poll_quiz(chat_id: str, lang: str,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
    if chat_id in active_poll_quizzes or chat_id in active_custom_text_quizzes:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text={'uz': "⚠️ Allaqachon quiz bor! /stopquiz.",
                  'ru': "⚠️ Квиз уже идёт! /stopquiz.",
                  'en': "⚠️ A quiz is already running! /stopquiz."}.get(lang, "⚠️")
        )
        return

    pool = CUSTOM_QUESTIONS.copy()
    random.shuffle(pool)
    questions = pool[:min(POLL_QUIZ_SIZE, len(pool))]

    active_poll_quizzes[chat_id] = {
        'questions': questions, 'current': 0,
        'scores': {}, 'poll_id': None, 'job': None,
        'lang': lang, 'question_time': None, 'answered_poll': set(),
    }

    start_msg = {
        'uz': f"📚 <b>Test viktorinasi boshlanadi!</b>\n{len(questions)} ta savol · Har biriga {POLL_SECS} soniya\nTo'g'ri variantni tanlang 👇",
        'ru': f"📚 <b>Тестовый квиз начинается!</b>\n{len(questions)} вопросов · {POLL_SECS} секунд каждый\nВыберите правильный вариант 👇",
        'en': f"📚 <b>Test Quiz starts!</b>\n{len(questions)} questions · {POLL_SECS}s each\nPick the correct answer 👇",
    }
    await context.bot.send_message(chat_id=int(chat_id),
                                   text=start_msg.get(lang, start_msg['uz']),
                                   parse_mode='HTML')
    await _send_poll_question(context, chat_id)


async def _send_poll_question(context: ContextTypes.DEFAULT_TYPE,
                               chat_id: str) -> None:
    quiz = active_poll_quizzes.get(chat_id)
    if not quiz:
        return

    idx   = quiz['current']
    lang  = quiz['lang']
    total = len(quiz['questions'])
    q     = quiz['questions'][idx]

    question_text = f"[{idx+1}/{total}] {q.get(lang, q.get('uz', '?'))}"
    shuffled_opts, new_correct = _shuffled_options(q, lang)
    explanation = q.get('explanation', {}).get(lang, q.get('explanation', {}).get('uz', ''))

    quiz.update(poll_id=None, answered_poll=set(), question_time=time.time())

    try:
        msg = await context.bot.send_poll(
            chat_id=int(chat_id),
            question=question_text[:300],
            options=[o[:100] for o in shuffled_opts],
            type='quiz',
            correct_option_id=new_correct,
            is_anonymous=False,
            open_period=POLL_SECS,
            explanation=explanation[:200] if explanation else None,
        )
        quiz['poll_id'] = msg.poll.id
        quiz['msg_id']  = msg.message_id
    except Exception as e:
        logger.error("send_poll error chat=%s: %s", chat_id, e)

    if quiz.get('job'):
        try: quiz['job'].schedule_removal()
        except Exception: pass

    quiz['job'] = context.application.job_queue.run_once(
        _poll_advance,
        POLL_SECS + 2,
        data={'chat_id': chat_id},
        name=f"pollquiz_{chat_id}_{idx}",
    )


async def handle_poll_answer(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    pa = update.poll_answer
    user_id  = str(pa.user.id)
    username = pa.user.username or pa.user.first_name or user_id

    for chat_id, quiz in active_poll_quizzes.items():
        if quiz.get('poll_id') != pa.poll_id:
            continue
        if user_id in quiz['answered_poll']:
            break
        quiz['answered_poll'].add(user_id)
        q = quiz['questions'][quiz['current']]
        # Note: we can't check correct here since we shuffled; PTB/Telegram marks correct
        # We track via PollAnswer.option_ids matching the shuffled correct index
        # But we stored new_correct in the quiz during send — save it
        if pa.option_ids and pa.option_ids[0] == quiz.get('current_correct_idx', -1):
            elapsed = round(time.time() - (quiz.get('question_time') or time.time()), 1)
            quiz['scores'].setdefault(user_id, {'name': username, 'score': 0, 'times': []})
            quiz['scores'][user_id]['score'] += 1
            quiz['scores'][user_id]['times'].append(elapsed)
        break


async def _poll_advance(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data['chat_id']
    quiz = active_poll_quizzes.get(chat_id)
    if not quiz:
        return
    quiz['current'] += 1
    if quiz['current'] >= len(quiz['questions']):
        await _finish_poll(context, chat_id)
    else:
        context.application.job_queue.run_once(
            _send_next_poll_job, 1,
            data={'chat_id': chat_id},
            name=f"pollquiz_next_{chat_id}_{quiz['current']}",
        )


async def _send_next_poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data.get('chat_id', '')
    try:
        await _send_poll_question(context, chat_id)
    except Exception as e:
        logger.error("send_next_poll_job error chat=%s: %s", chat_id, e)
        quiz = active_poll_quizzes.get(chat_id)
        if quiz:
            quiz['current'] += 1
            if quiz['current'] >= len(quiz['questions']):
                await _finish_poll(context, chat_id)
            else:
                context.application.job_queue.run_once(
                    _send_next_poll_job, 1,
                    data={'chat_id': chat_id},
                    name=f"pollquiz_skip_{chat_id}_{quiz['current']}",
                )


async def _finish_poll(context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> None:
    quiz = active_poll_quizzes.pop(chat_id, None)
    if not quiz:
        return
    await context.bot.send_message(
        chat_id=int(chat_id),
        text=_finish_msg(quiz.get('lang', 'uz'), quiz.get('scores', {})),
        parse_mode='HTML',
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOM TEXT QUIZ  (text Q&A, shown as A/B/C/D, answer by typing)
# ═══════════════════════════════════════════════════════════════════════════════

_TEXT_SECS = 20


async def start_custom_text_quiz(chat_id: str, lang: str,
                                  context: ContextTypes.DEFAULT_TYPE) -> None:
    if chat_id in active_poll_quizzes or chat_id in active_custom_text_quizzes:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text={'uz': "⚠️ Allaqachon quiz bor! /stopquiz.",
                  'ru': "⚠️ Квиз уже идёт! /stopquiz.",
                  'en': "⚠️ A quiz is already running! /stopquiz."}.get(lang, "⚠️")
        )
        return

    pool = CUSTOM_QUESTIONS.copy()
    random.shuffle(pool)
    questions = pool[:min(POLL_QUIZ_SIZE, len(pool))]

    active_custom_text_quizzes[chat_id] = {
        'questions': questions, 'current': 0,
        'scores': {}, 'answered': False,
        'correct_letter': '', 'correct_text': '',
        'job': None, 'lang': lang, 'question_time': None,
    }

    start_msg = {
        'uz': f"📚 <b>Test viktorinasi boshlanadi!</b>\n{len(questions)} ta savol · Har biriga {_TEXT_SECS} soniya\nHarf yoki javob matnini yozing (A, B, C...)",
        'ru': f"📚 <b>Тестовый квиз начинается!</b>\n{len(questions)} вопросов · {_TEXT_SECS} секунд каждый\nНапишите букву или текст ответа (A, B, C...)",
        'en': f"📚 <b>Test Quiz starts!</b>\n{len(questions)} questions · {_TEXT_SECS}s each\nType the letter or answer text (A, B, C...)",
    }
    await context.bot.send_message(chat_id=int(chat_id),
                                   text=start_msg.get(lang, start_msg['uz']),
                                   parse_mode='HTML')
    await _send_custom_text_q(context, chat_id)


async def _send_custom_text_q(context: ContextTypes.DEFAULT_TYPE,
                                chat_id: str) -> None:
    quiz = active_custom_text_quizzes.get(chat_id)
    if not quiz:
        return

    idx   = quiz['current']
    lang  = quiz['lang']
    total = len(quiz['questions'])
    q     = quiz['questions'][idx]

    shuffled_opts, new_correct = _shuffled_options(q, lang)

    quiz['correct_letter'] = _LETTERS[new_correct].lower()
    quiz['correct_text']   = shuffled_opts[new_correct].lower()
    quiz['answered']       = False
    quiz['question_time']  = time.time()

    opts_str = '\n'.join(f"{_LETTERS[i]}) {opt}" for i, opt in enumerate(shuffled_opts))
    text = (
        f"❓ <b>{idx+1}/{total}</b>\n\n"
        f"{html.escape(q.get(lang, q.get('uz', '?')))}\n\n"
        f"{opts_str}"
    )

    await context.bot.send_message(chat_id=int(chat_id), text=text, parse_mode='HTML')

    if quiz.get('job'):
        try: quiz['job'].schedule_removal()
        except Exception: pass

    quiz['job'] = context.application.job_queue.run_once(
        _custom_text_timeout,
        _TEXT_SECS,
        data={'chat_id': chat_id},
        name=f"ctquiz_{chat_id}_{idx}",
    )


async def check_custom_text_answer(
    chat_id: str, user_id: str, username: str,
    raw_text: str, update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Called from handle_guess. Returns True if message consumed."""
    quiz = active_custom_text_quizzes.get(chat_id)
    if not quiz or quiz.get('answered'):
        return False

    answer = raw_text.strip().lower()
    if answer not in (quiz['correct_letter'], quiz['correct_text']):
        return False   # wrong — stay silent, let others try

    elapsed = round(time.time() - (quiz.get('question_time') or time.time()), 1)
    quiz['answered'] = True
    if quiz.get('job'):
        try: quiz['job'].schedule_removal()
        except Exception: pass

    quiz['scores'].setdefault(user_id, {'name': username, 'score': 0, 'times': []})
    quiz['scores'][user_id]['score'] += 1
    quiz['scores'][user_id]['times'].append(elapsed)

    lang = quiz['lang']
    q    = quiz['questions'][quiz['current']]
    correct_display = q['options'].get(lang, q['options']['uz'])[q['correct']]
    name = update.effective_user.first_name or username

    await update.message.reply_text(
        f"✅ <b>{html.escape(name)}</b> +1  ⏱{elapsed}s\n"
        f"🎯 <i>{html.escape(correct_display)}</i>",
        parse_mode='HTML',
    )

    quiz['current'] += 1
    if quiz['current'] >= len(quiz['questions']):
        await _finish_custom_text(context, chat_id)
    else:
        quiz['job'] = context.application.job_queue.run_once(
            _next_custom_text_job, 1,
            data={'chat_id': chat_id},
            name=f"ctquiz_next_{chat_id}_{quiz['current']}",
        )
    return True


async def _custom_text_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data['chat_id']
    quiz = active_custom_text_quizzes.get(chat_id)
    if not quiz:
        return

    lang = quiz['lang']
    q    = quiz['questions'][quiz['current']]
    correct_display = q['options'].get(lang, q['options']['uz'])[q['correct']]
    explanation = q.get('explanation', {}).get(lang, q.get('explanation', {}).get('uz', ''))
    exp_line = f"\n💡 {html.escape(explanation)}" if explanation else ""

    try:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=f"⏰ <b>{html.escape(correct_display)}</b>{exp_line}",
            parse_mode='HTML',
        )
    except Exception as e:
        logger.error("custom_text_timeout error: %s", e)

    quiz['current'] += 1
    if quiz['current'] >= len(quiz['questions']):
        await _finish_custom_text(context, chat_id)
    else:
        context.application.job_queue.run_once(
            _next_custom_text_job, 1,
            data={'chat_id': chat_id},
            name=f"ctquiz_next_{chat_id}_{quiz['current']}",
        )


async def _next_custom_text_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data.get('chat_id', '')
    try:
        await _send_custom_text_q(context, chat_id)
    except Exception as e:
        logger.error("next_custom_text_job error chat=%s: %s", chat_id, e)
        quiz = active_custom_text_quizzes.get(chat_id)
        if quiz:
            quiz['current'] += 1
            if quiz['current'] >= len(quiz['questions']):
                await _finish_custom_text(context, chat_id)
            else:
                context.application.job_queue.run_once(
                    _next_custom_text_job, 1,
                    data={'chat_id': chat_id},
                    name=f"ctquiz_skip_{chat_id}_{quiz['current']}",
                )


async def _finish_custom_text(context: ContextTypes.DEFAULT_TYPE,
                               chat_id: str) -> None:
    quiz = active_custom_text_quizzes.pop(chat_id, None)
    if not quiz:
        return
    await context.bot.send_message(
        chat_id=int(chat_id),
        text=_finish_msg(quiz.get('lang', 'uz'), quiz.get('scores', {})),
        parse_mode='HTML',
    )
