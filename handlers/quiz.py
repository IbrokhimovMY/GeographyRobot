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

from data import (
    COUNTRIES, COUNTRIES_CAPITALS, COUNTRY_FLAGS,
    COUNTRY_CURRENCIES, COUNTRY_CONTINENTS,
)
from database import get_user_lang
from keyboards import default_kb
from translations import get_country_name
from geo_facts import MOUNTAIN_FACTS, RIVER_FACTS, LAKE_FACTS, GEO_RECORDS

logger = logging.getLogger(__name__)

QUIZ_SIZE      = 20
VARIANT_SECS   = 15   # seconds per variant question
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


def _countries_with_capitals() -> list[str]:
    return [c for c in COUNTRIES if COUNTRIES_CAPITALS.get(c)]


def _make_choices(correct_uz: str, n: int = 4) -> tuple[list[str], int]:
    """(capital_list, correct_index)  for a variant question."""
    pool = [c for c in COUNTRIES if c != correct_uz and COUNTRIES_CAPITALS.get(c)]
    decoys = random.sample(pool, min(n - 1, len(pool)))
    bucket = decoys + [correct_uz]
    random.shuffle(bucket)
    idx = bucket.index(correct_uz)
    return [COUNTRIES_CAPITALS.get(c, '?') for c in bucket], idx


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


_CONTINENTS = {
    'africa':        {'uz': 'Afrika',          'ru': 'Африка',           'en': 'Africa'},
    'asia':          {'uz': 'Osiyo',            'ru': 'Азия',             'en': 'Asia'},
    'europe':        {'uz': 'Yevropa',          'ru': 'Европа',           'en': 'Europe'},
    'north_america': {'uz': 'Shimoliy Amerika', 'ru': 'Северная Америка', 'en': 'North America'},
    'south_america': {'uz': 'Janubiy Amerika',  'ru': 'Южная Америка',    'en': 'South America'},
    'oceania':       {'uz': 'Okeaniya',         'ru': 'Океания',          'en': 'Oceania'},
}

_Q = {
    'uz': {
        'ask_capital':   "🏙 Poytaxti qaysi?",
        'ask_flag':      "Bu qaysi davlatning bayrog'i?",
        'ask_currency':  "Bu valyuta qaysi davlatda ishlatiladi?",
        'ask_continent': "Bu davlat qaysi qit'ada?",
        'ask_country':   "Bu qaysi davlat?",
    },
    'ru': {
        'ask_capital':   "🏙 Какова столица?",
        'ask_flag':      "Флаг какой страны?",
        'ask_currency':  "Какая страна использует эту валюту?",
        'ask_continent': "В каком континенте эта страна?",
        'ask_country':   "Что за страна?",
    },
    'en': {
        'ask_capital':   "🏙 What is the capital?",
        'ask_flag':      "Which country has this flag?",
        'ask_currency':  "Which country uses this currency?",
        'ask_continent': "Which continent is this country in?",
        'ask_country':   "Which country is it?",
    },
}


def _qask(lang: str, key: str) -> str:
    return _Q.get(lang, _Q['en']).get(key, key)


def _cont_name(key: str, lang: str) -> str:
    return _CONTINENTS.get(key, {}).get(lang) or _CONTINENTS.get(key, {}).get('en', key)


def _make_country_choices(correct_uz: str, lang: str, n: int = 4) -> tuple[list[str], int]:
    """Returns (country-name list, correct_index) for flag/currency/continent questions."""
    pool = [c for c in COUNTRIES if c != correct_uz]
    decoys = random.sample(pool, min(n - 1, len(pool)))
    bucket = decoys + [correct_uz]
    random.shuffle(bucket)
    idx = bucket.index(correct_uz)
    return [get_country_name(c, lang) for c in bucket], idx


def _continent_choices(correct_uz: str, lang: str) -> tuple[list[str], int]:
    correct_cont = COUNTRY_CONTINENTS.get(correct_uz, 'asia')
    wrong = [c for c in _CONTINENTS if c != correct_cont]
    bucket = random.sample(wrong, min(3, len(wrong))) + [correct_cont]
    random.shuffle(bucket)
    idx = bucket.index(correct_cont)
    return [_cont_name(c, lang) for c in bucket], idx


def _geo_country_choices(correct_uz: str, lang: str, n: int = 4) -> tuple[list[str], int]:
    """4 country-name choices where correct_uz is one of them."""
    pool = [c for c in COUNTRIES if c != correct_uz]
    decoys = random.sample(pool, min(n - 1, len(pool)))
    bucket = decoys + [correct_uz]
    random.shuffle(bucket)
    idx = bucket.index(correct_uz)
    return [get_country_name(c, lang) for c in bucket], idx


# Pre-filter facts to only those whose country exists in COUNTRIES
_COUNTRIES_SET = set(COUNTRIES)
_VALID_MOUNTAINS = [(n, c) for n, c in MOUNTAIN_FACTS if c in _COUNTRIES_SET]
_VALID_RIVERS    = [(n, c) for n, c in RIVER_FACTS    if c in _COUNTRIES_SET]
_VALID_LAKES     = [(n, c) for n, c in LAKE_FACTS     if c in _COUNTRIES_SET]


def _ask_geo(lang: str, geo_type: str) -> str:
    q = {
        'mountain': {'uz': "⛰ Bu tog' qaysi davlatda joylashgan?",
                     'ru': "⛰ В какой стране находится эта гора?",
                     'en': "⛰ In which country is this mountain located?"},
        'river':    {'uz': "🌊 Bu daryo qaysi davlat hududidan oqadi?",
                     'ru': "🌊 Через какую страну протекает эта река?",
                     'en': "🌊 Which country does this river flow through?"},
        'lake':     {'uz': "🏞 Bu ko'l qaysi davlatda joylashgan?",
                     'ru': "🏞 В какой стране находится это озеро?",
                     'en': "🏞 In which country is this lake located?"},
    }
    return q.get(geo_type, {}).get(lang, q.get(geo_type, {}).get('en', '?'))


def _build_geo_question(q_num: int, lang: str) -> dict | None:
    """Build mountain/river/lake/record question. Returns None if no valid facts."""
    pool = []
    if _VALID_MOUNTAINS: pool.append('mountain')
    if _VALID_RIVERS:    pool.append('river')
    if _VALID_LAKES:     pool.append('lake')
    if GEO_RECORDS:      pool.append('record')
    if not pool:
        return None

    geo_type = random.choice(pool)
    num = f"<b>{q_num}/{QUIZ_SIZE}</b>"

    if geo_type == 'record':
        rec = random.choice(GEO_RECORDS)
        choices = rec['choices'].get(lang, rec['choices']['en'])
        cidx = rec['correct']
        q_text = f"❓ {num}\n\n{rec.get(lang, rec['en'])}"
        return {
            'text': q_text, 'choices': list(choices),
            'correct_idx': cidx, 'answer': choices[cidx],
            'geo_type': 'record', 'correct_uz': None,
        }

    if geo_type == 'mountain':
        name, country_uz = random.choice(_VALID_MOUNTAINS)
        choices, cidx = _geo_country_choices(country_uz, lang)
        q_text = f"❓ {num}\n\n⛰ <b>{html.escape(name)}</b>\n\n{_ask_geo(lang, 'mountain')}"
    elif geo_type == 'river':
        name, country_uz = random.choice(_VALID_RIVERS)
        choices, cidx = _geo_country_choices(country_uz, lang)
        q_text = f"❓ {num}\n\n🌊 <b>{html.escape(name)}</b>\n\n{_ask_geo(lang, 'river')}"
    else:  # lake
        name, country_uz = random.choice(_VALID_LAKES)
        choices, cidx = _geo_country_choices(country_uz, lang)
        q_text = f"❓ {num}\n\n🏞 <b>{html.escape(name)}</b>\n\n{_ask_geo(lang, 'lake')}"

    return {
        'text': q_text, 'choices': choices,
        'correct_idx': cidx, 'answer': choices[cidx],
        'geo_type': geo_type, 'correct_uz': country_uz,
    }


def _build_geo_text_question(q_num: int, lang: str) -> tuple[str, str] | None:
    """Build mountain/river/lake text question. Returns (question_text, correct_uz)."""
    pool = []
    if _VALID_MOUNTAINS: pool.append('mountain')
    if _VALID_RIVERS:    pool.append('river')
    if _VALID_LAKES:     pool.append('lake')
    if not pool:
        return None

    geo_type = random.choice(pool)
    num = f"<b>{q_num}/{QUIZ_SIZE}</b>"

    if geo_type == 'mountain':
        name, country_uz = random.choice(_VALID_MOUNTAINS)
        text = f"❓ {num}\n\n⛰ <b>{html.escape(name)}</b>\n\n{_ask_geo(lang, 'mountain')}"
    elif geo_type == 'river':
        name, country_uz = random.choice(_VALID_RIVERS)
        text = f"❓ {num}\n\n🌊 <b>{html.escape(name)}</b>\n\n{_ask_geo(lang, 'river')}"
    else:
        name, country_uz = random.choice(_VALID_LAKES)
        text = f"❓ {num}\n\n🏞 <b>{html.escape(name)}</b>\n\n{_ask_geo(lang, 'lake')}"

    return text, country_uz


def _build_variant_question(country_uz: str, q_num: int, lang: str) -> dict:
    """Pick a random question type, return {text, choices, correct_idx, answer_text}."""
    # 1 in 3 chance of a mountain/river/lake/record question
    if random.randint(1, 3) == 1:
        geo = _build_geo_question(q_num, lang)
        if geo:
            return geo

    flag = COUNTRY_FLAGS.get(country_uz, '🌍')
    cname = get_country_name(country_uz, lang)
    num = f"<b>{q_num}/{QUIZ_SIZE}</b>"

    types = ['continent']
    if COUNTRIES_CAPITALS.get(country_uz):
        types.append('capital')
    if COUNTRY_FLAGS.get(country_uz):
        types.append('flag')
    cur = COUNTRY_CURRENCIES.get(country_uz)
    if cur and cur[0]:
        types.append('currency')

    qtype = random.choice(types)

    if qtype == 'capital':
        choices, cidx = _make_choices(country_uz)
        ask = _qask(lang, 'ask_capital')
        text = f"❓ {num}\n\n{flag} <b>{html.escape(cname)}</b>\n\n{ask}"
        answer = COUNTRIES_CAPITALS.get(country_uz, '?')

    elif qtype == 'flag':
        choices, cidx = _make_country_choices(country_uz, lang)
        ask = _qask(lang, 'ask_flag')
        text = f"❓ {num}\n\n{flag}\n\n{ask}"
        answer = cname

    elif qtype == 'currency':
        cur_name, cur_code = cur
        choices, cidx = _make_country_choices(country_uz, lang)
        ask = _qask(lang, 'ask_currency')
        text = f"❓ {num}\n\n💵 <b>{html.escape(cur_name)}</b> (<code>{cur_code}</code>)\n\n{ask}"
        answer = cname

    else:  # continent
        choices, cidx = _continent_choices(country_uz, lang)
        ask = _qask(lang, 'ask_continent')
        text = f"❓ {num}\n\n{flag} <b>{html.escape(cname)}</b>\n\n{ask}"
        correct_cont = COUNTRY_CONTINENTS.get(country_uz, 'asia')
        answer = _cont_name(correct_cont, lang)

    return {'text': text, 'choices': choices, 'correct_idx': cidx, 'answer': answer}


def _build_text_question(country_uz: str, q_num: int, lang: str) -> tuple[str, str]:
    """Returns (question_text, correct_uz). Answer is always a country name."""
    # 1 in 3 chance of a mountain/river/lake question (answer = country name)
    if random.randint(1, 3) == 1:
        geo = _build_geo_text_question(q_num, lang)
        if geo:
            return geo  # (text, country_uz from geo fact)

    flag = COUNTRY_FLAGS.get(country_uz, '🌍')
    num = f"<b>{q_num}/{QUIZ_SIZE}</b>"
    ask = _qask(lang, 'ask_country')

    types = []
    if COUNTRIES_CAPITALS.get(country_uz):
        types.append('capital')
    if COUNTRY_FLAGS.get(country_uz):
        types.append('flag')
    cur = COUNTRY_CURRENCIES.get(country_uz)
    if cur and cur[0]:
        types.append('currency')
    if not types:
        types = ['capital']

    qtype = random.choice(types)

    if qtype == 'capital':
        cap = COUNTRIES_CAPITALS.get(country_uz, '?')
        return f"❓ {num}\n\n🏙 <b>{html.escape(cap)}</b> {flag}\n\n{ask}", country_uz

    elif qtype == 'flag':
        return f"❓ {num}\n\n{flag}\n\n{ask}", country_uz

    else:  # currency
        cur_name, cur_code = cur
        return f"❓ {num}\n\n💵 <b>{html.escape(cur_name)}</b> (<code>{cur_code}</code>) {flag}\n\n{ask}", country_uz


def _quiz_i18n(lang: str, key: str, **kw) -> str:
    strings = {
        'uz': {
            'variant_start': "🎮 <b>Viktorina boshlanadi!</b>\n20 ta savol · Har biriga 15 soniya\nVariantlardan birini tanlang 👇",
            'text_start':    "🎮 <b>Viktorina boshlanadi!</b>\n20 ta savol · Har biriga 15 soniya\nJavobni yozing, birinchi to'g'ri javob ball oladi!",
            'correct_ans':   "✅ {label} <b>{answer}</b>",
            'first_correct': "✅ <b>{name}</b> +1 · {flag} <b>{country}</b>",
            'timeout':       "⏰ {flag} <b>{country}</b>",
            'results':       "🏆 <b>Viktorina tugadi!</b>\n\n{board}",
            'no_scores':     "Hech kim to'g'ri javob bermadi.",
            'already':       "⚠️ Allaqachon quiz bor!",
            'stopped':       "✅ Quiz to'xtatildi.",
            'none':          "Faol quiz yo'q.",
        },
        'ru': {
            'variant_start': "🎮 <b>Квиз начинается!</b>\n20 вопросов · 15 секунд на каждый\nВыберите один из вариантов 👇",
            'text_start':    "🎮 <b>Квиз начинается!</b>\n20 вопросов · 15 секунд на каждый\nПишите ответ, первый правильный получает балл!",
            'correct_ans':   "✅ {label} <b>{answer}</b>",
            'first_correct': "✅ <b>{name}</b> +1 · {flag} <b>{country}</b>",
            'timeout':       "⏰ {flag} <b>{country}</b>",
            'results':       "🏆 <b>Квиз завершён!</b>\n\n{board}",
            'no_scores':     "Никто не ответил правильно.",
            'already':       "⚠️ Квиз уже идёт!",
            'stopped':       "✅ Квиз остановлен.",
            'none':          "Нет активного квиза.",
        },
        'en': {
            'variant_start': "🎮 <b>Quiz starts!</b>\n20 questions · 15 seconds each\nPick one of the options 👇",
            'text_start':    "🎮 <b>Quiz starts!</b>\n20 questions · 15 seconds each\nType your answer — first correct wins a point!",
            'correct_ans':   "✅ {label} <b>{answer}</b>",
            'first_correct': "✅ <b>{name}</b> +1 · {flag} <b>{country}</b>",
            'timeout':       "⏰ {flag} <b>{country}</b>",
            'results':       "🏆 <b>Quiz finished!</b>\n\n{board}",
            'no_scores':     "Nobody answered correctly.",
            'already':       "⚠️ A quiz is already running!",
            'stopped':       "✅ Quiz stopped.",
            'none':          "No active quiz.",
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

    questions = random.sample(COUNTRIES, min(QUIZ_SIZE, len(COUNTRIES)))
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

    idx  = quiz['current']
    lang = quiz['lang']
    cuz  = quiz['questions'][idx]

    q = _build_variant_question(cuz, idx + 1, lang)
    # geo questions may have a different correct country than the quiz country
    effective_correct_uz = q.get('correct_uz') or cuz
    quiz.update(correct_idx=q['correct_idx'], correct_uz=effective_correct_uz,
                correct_answer=q['answer'], answered=set())

    choices = q['choices']
    full_text = q['text'] + '\n\n' + '\n'.join(
        f"{_LABELS[i]} {html.escape(c)}" for i, c in enumerate(choices)
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{_LABELS[i]} {c[:28]}", callback_data=f"vq:{chat_id}:{i}")
         for i, c in enumerate(choices[:2])],
        [InlineKeyboardButton(f"{_LABELS[i]} {c[:28]}", callback_data=f"vq:{chat_id}:{i}")
         for i, c in enumerate(choices[2:], 2)],
    ])

    msg = await context.bot.send_message(
        chat_id=int(chat_id), text=full_text, parse_mode='HTML', reply_markup=kb
    )
    quiz['msg_id'] = msg.message_id

    if quiz.get('job'):
        try: quiz['job'].schedule_removal()
        except Exception: pass
    quiz['job'] = context.application.job_queue.run_once(
        _variant_timeout,
        VARIANT_SECS,
        data={'chat_id': chat_id},
        name=f"vquiz_{chat_id}_{idx}",   # unique per question — avoids name conflict
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
    label  = _LABELS[quiz['correct_idx']]
    answer = quiz.get('correct_answer', '?')

    # Remove inline keyboard from question message
    if quiz.get('msg_id'):
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=int(chat_id), message_id=quiz['msg_id'], reply_markup=None
            )
        except Exception:
            pass

    try:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=_quiz_i18n(lang, 'correct_ans', label=label, answer=html.escape(answer)),
            parse_mode='HTML',
        )
    except Exception as e:
        logger.error("variant_timeout send error: %s", e)

    quiz['current'] += 1
    if quiz['current'] >= QUIZ_SIZE:
        await _finish(context, chat_id, 'variant')
    else:
        # Schedule as a NEW separate job — never call _send_variant_q directly
        # from inside a job callback to avoid PTB job-chain issues
        next_idx = quiz['current']
        context.application.job_queue.run_once(
            _variant_q_job,
            1,
            data={'chat_id': chat_id},
            name=f"vquiz_next_{chat_id}_{next_idx}",  # unique per question
        )


async def _variant_q_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bridge job so _send_variant_q is always called from a fresh job context."""
    chat_id = context.job.data.get('chat_id', '')
    try:
        await _send_variant_q(context, chat_id)
    except Exception as e:
        logger.error("variant_q_job error chat=%s: %s", chat_id, e)
        quiz = active_variant_quizzes.get(chat_id)
        if quiz:
            quiz['current'] += 1
            if quiz['current'] >= QUIZ_SIZE:
                await _finish(context, chat_id, 'variant')
            else:
                context.application.job_queue.run_once(
                    _variant_q_job, 1,
                    data={'chat_id': chat_id},
                    name=f"vquiz_skip_{chat_id}_{quiz['current']}",
                )


# ──────────────────────────────────────────────────────────────────────────────
#  TYPE 2 — TEXT (free-text, first correct wins)
# ──────────────────────────────────────────────────────────────────────────────

async def start_text_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat(update)
    lang = get_user_lang(_uid(update))

    if chat_id in active_variant_quizzes or chat_id in active_text_quizzes:
        await update.message.reply_text(_quiz_i18n(lang, 'already'))
        return

    pool = _countries_with_capitals()
    questions = random.sample(pool, min(QUIZ_SIZE, len(pool)))
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

    text, correct_uz = _build_text_question(cuz, idx + 1, lang)
    quiz.update(correct_uz=correct_uz, answered=False)

    await context.bot.send_message(chat_id=int(chat_id), text=text, parse_mode='HTML')

    if quiz.get('job'):
        try: quiz['job'].schedule_removal()
        except Exception: pass
    quiz['job'] = context.application.job_queue.run_once(
        _text_timeout,
        TEXT_SECS,
        data={'chat_id': chat_id},
        name=f"tquiz_{chat_id}_{idx}",  # unique per question
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
        try: quiz['job'].schedule_removal()
        except Exception: pass

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
        next_idx = quiz['current']
        quiz['job'] = context.application.job_queue.run_once(
            _next_text_q_job,
            1,                                          # 1s gap then next question
            data={'chat_id': chat_id},
            name=f"tquiz_next_{chat_id}_{next_idx}",   # unique per question
        )
    return True


async def _next_text_q_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data.get('chat_id', '')
    try:
        await _send_text_q(context, chat_id)
    except Exception as e:
        logger.error("next_text_q_job error chat=%s: %s", chat_id, e)
        quiz = active_text_quizzes.get(chat_id)
        if quiz:
            quiz['current'] += 1
            if quiz['current'] >= QUIZ_SIZE:
                await _finish(context, chat_id, 'text')
            else:
                context.application.job_queue.run_once(
                    _next_text_q_job, 1,
                    data={'chat_id': chat_id},
                    name=f"tquiz_skip_{chat_id}_{quiz['current']}",
                )


async def _text_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    chat_id = data['chat_id']
    quiz = active_text_quizzes.get(chat_id)
    if not quiz:
        return

    lang = quiz['lang']
    cuz  = quiz['correct_uz']
    flag = COUNTRY_FLAGS.get(cuz, '🌍')

    try:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=_quiz_i18n(lang, 'timeout',
                            flag=flag,
                            country=html.escape(get_country_name(cuz, lang))),
            parse_mode='HTML',
        )
    except Exception as e:
        logger.error("text_timeout send error: %s", e)

    quiz['current'] += 1
    if quiz['current'] >= QUIZ_SIZE:
        await _finish(context, chat_id, 'text')
    else:
        next_idx = quiz['current']
        context.application.job_queue.run_once(
            _next_text_q_job,
            1,
            data={'chat_id': chat_id},
            name=f"tquiz_next_{chat_id}_{next_idx}",  # unique per question
        )


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
