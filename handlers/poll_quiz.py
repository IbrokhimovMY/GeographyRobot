"""
Native Telegram Quiz Poll mode (sendPoll type='quiz').
Looks like the classic anonymous quiz polls in channels.
"""
import html
import logging
import random
import time

from telegram import Update
from telegram.ext import ContextTypes

from custom_quiz_data import CUSTOM_QUESTIONS
from database import get_user_lang
from translations import get_country_name

logger = logging.getLogger(__name__)

POLL_QUIZ_SIZE = 20
POLL_SECS      = 20   # seconds each poll stays open

# chat_id → quiz state
active_poll_quizzes: dict = {}


# ─── helpers ─────────────────────────────────────────────────────────────────

def _uid(u: Update) -> str: return str(u.effective_user.id)
def _chat(u: Update) -> str: return str(u.effective_chat.id)


def _scoreboard(scores: dict) -> str:
    if not scores:
        return "—"
    medals = ['🥇', '🥈', '🥉']
    rows = sorted(scores.items(), key=lambda x: (-x[1]['score'], _avg(x[1])))
    lines = []
    for i, (_, d) in enumerate(rows[:10]):
        med = medals[i] if i < 3 else f"{i+1}."
        avg = _avg(d)
        t = f"  ⏱{avg:.1f}s" if d.get('times') else ""
        lines.append(f"{med} <b>{html.escape(d['name'])}</b> — {d['score']}{t}")
    return '\n'.join(lines) if lines else "—"


def _avg(d: dict) -> float:
    t = d.get('times', [])
    return sum(t) / len(t) if t else 999.0


# ─── start ───────────────────────────────────────────────────────────────────

async def start_poll_quiz(chat_id: str, lang: str,
                          context: ContextTypes.DEFAULT_TYPE) -> None:
    if chat_id in active_poll_quizzes:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text="⚠️ Quiz already running! /stopquiz to stop." if lang == 'en'
                 else ("⚠️ Allaqachon quiz bor! /stopquiz." if lang == 'uz'
                       else "⚠️ Квиз уже идёт! /stopquiz.")
        )
        return

    pool = CUSTOM_QUESTIONS.copy()
    random.shuffle(pool)
    questions = pool[:min(POLL_QUIZ_SIZE, len(pool))]

    active_poll_quizzes[chat_id] = {
        'questions': questions, 'current': 0,
        'scores': {}, 'poll_id': None,
        'job': None, 'lang': lang,
        'question_time': None,
        'answered_poll': set(),  # user_ids who answered current poll
    }

    start_msg = {
        'uz': f"📚 <b>Test viktorinasi boshlanadi!</b>\n{len(questions)} ta savol · Har biriga {POLL_SECS} soniya\nTo'g'ri variantni tanlang 👇",
        'ru': f"📚 <b>Тестовый квиз начинается!</b>\n{len(questions)} вопросов · {POLL_SECS} секунд каждый\nВыберите правильный вариант 👇",
        'en': f"📚 <b>Test Quiz starts!</b>\n{len(questions)} questions · {POLL_SECS} seconds each\nSelect the correct answer 👇",
    }
    await context.bot.send_message(
        chat_id=int(chat_id),
        text=start_msg.get(lang, start_msg['uz']),
        parse_mode='HTML',
    )
    await _send_poll_question(context, chat_id)


async def _send_poll_question(context: ContextTypes.DEFAULT_TYPE,
                               chat_id: str) -> None:
    quiz = active_poll_quizzes.get(chat_id)
    if not quiz:
        return

    idx  = quiz['current']
    lang = quiz['lang']
    total = len(quiz['questions'])
    q    = quiz['questions'][idx]

    question_text = f"[{idx + 1}/{total}] {q.get(lang, q.get('uz', '?'))}"
    options = q['options'].get(lang, q['options'].get('uz', []))
    correct = q['correct']
    explanation = q.get('explanation', {}).get(lang, q.get('explanation', {}).get('uz', ''))

    quiz.update(poll_id=None, answered_poll=set(), question_time=time.time())

    try:
        msg = await context.bot.send_poll(
            chat_id=int(chat_id),
            question=question_text[:300],
            options=[o[:100] for o in options],
            type='quiz',
            correct_option_id=correct,
            is_anonymous=False,      # so we can track who answered correctly
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
        POLL_SECS + 2,    # wait for poll to close + 2s buffer
        data={'chat_id': chat_id},
        name=f"pollquiz_{chat_id}_{idx}",
    )


async def handle_poll_answer(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called for every PollAnswer — records correct answerers and their timing."""
    pa = update.poll_answer
    poll_id  = pa.poll_id
    user_id  = str(pa.user.id)
    username = pa.user.username or pa.user.first_name or user_id

    for chat_id, quiz in active_poll_quizzes.items():
        if quiz.get('poll_id') != poll_id:
            continue
        if user_id in quiz['answered_poll']:
            break  # already recorded
        quiz['answered_poll'].add(user_id)

        q = quiz['questions'][quiz['current']]
        if pa.option_ids and pa.option_ids[0] == q['correct']:
            elapsed = round(time.time() - (quiz.get('question_time') or time.time()), 1)
            quiz['scores'].setdefault(user_id, {'name': username, 'score': 0, 'times': []})
            quiz['scores'][user_id]['score'] += 1
            quiz['scores'][user_id]['times'].append(elapsed)
        break


async def _poll_advance(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job: close current poll and move to next question."""
    data = context.job.data
    chat_id = data['chat_id']
    quiz = active_poll_quizzes.get(chat_id)
    if not quiz:
        return

    quiz['current'] += 1
    if quiz['current'] >= len(quiz['questions']):
        await _finish_poll_quiz(context, chat_id)
    else:
        quiz['job'] = context.application.job_queue.run_once(
            _send_next_poll_job,
            1,
            data={'chat_id': chat_id},
            name=f"pollquiz_next_{chat_id}_{quiz['current']}",
        )


async def _send_next_poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await _send_poll_question(context, context.job.data['chat_id'])
    except Exception as e:
        chat_id = context.job.data.get('chat_id', '?')
        logger.error("send_next_poll_job error chat=%s: %s", chat_id, e)
        quiz = active_poll_quizzes.get(chat_id)
        if quiz:
            quiz['current'] += 1
            if quiz['current'] >= len(quiz['questions']):
                await _finish_poll_quiz(context, chat_id)
            else:
                context.application.job_queue.run_once(
                    _send_next_poll_job, 1,
                    data={'chat_id': chat_id},
                    name=f"pollquiz_skip_{chat_id}_{quiz['current']}",
                )


async def _finish_poll_quiz(context: ContextTypes.DEFAULT_TYPE,
                             chat_id: str) -> None:
    quiz = active_poll_quizzes.pop(chat_id, None)
    if not quiz:
        return

    lang   = quiz.get('lang', 'uz')
    scores = quiz.get('scores', {})
    board  = _scoreboard(scores)

    title = {
        'uz': "🏆 <b>Test viktorinasi tugadi!</b>",
        'ru': "🏆 <b>Тестовый квиз завершён!</b>",
        'en': "🏆 <b>Test Quiz finished!</b>",
    }.get(lang, "🏆 <b>Test viktorinasi tugadi!</b>")

    no_scores = {
        'uz': "Hech kim to'g'ri javob bermadi.",
        'ru': "Никто не ответил правильно.",
        'en': "Nobody answered correctly.",
    }.get(lang, "")

    await context.bot.send_message(
        chat_id=int(chat_id),
        text=f"{title}\n\n{board if scores else no_scores}",
        parse_mode='HTML',
    )


def stop_poll_quiz(chat_id: str) -> bool:
    """Stop an active poll quiz. Returns True if one was stopped."""
    quiz = active_poll_quizzes.pop(chat_id, None)
    if quiz:
        if quiz.get('job'):
            try: quiz['job'].schedule_removal()
            except Exception: pass
        return True
    return False
