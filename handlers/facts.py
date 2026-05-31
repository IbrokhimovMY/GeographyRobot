"""
Daily geography facts — 'On This Day' style: a geographic event
that happened on today's date in history.

Country Wikipedia info stays in /info; here we show real calendar facts.
"""
import datetime
import html
import logging
import random
import urllib.parse

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from data import COUNTRIES, MAP_EN_TO_UZ
from database import get_daily_facts_subscribers, toggle_daily_facts, get_user_lang
from keyboards import default_kb
from translations import t, get_country_name, COUNTRY_NAMES_EN

logger = logging.getLogger(__name__)

_UZ_TO_EN: dict[str, str] = {uz: en for en, uz in MAP_EN_TO_UZ.items()}
_UZ_TO_EN.update(COUNTRY_NAMES_EN)

# Wikipedia requires a proper User-Agent — cloud IPs are 403'd without it
_WIKI_HEADERS = {
    "User-Agent": "MYGeoRobot/1.0 (Geography quiz Telegram bot; ibrokhimovmy@gmail.com)",
    "Accept": "application/json",
}

# Keywords to detect geographic relevance in "On This Day" events
_GEO_KEYWORDS = [
    # English
    "country", "island", "mountain", "river", "ocean", "sea", "lake", "continent",
    "discover", "explor", "independence", "founded", "capital", "earthquake",
    "volcano", "expedition", "territory", "border", "nation", "republic",
    "gulf", "bay", "peninsula", "strait", "desert", "forest", "glacier",
    # Russian
    "страна", "остров", "гора", "река", "океан", "море", "озеро",
    "независимость", "открыт", "экспедиция", "вулкан", "землетрясение",
    # Uzbek (rare but possible)
    "davlat", "orol", "tog", "daryo", "okean", "ko'l", "mustaqillik",
]

# Translated month names for display
_MONTHS = {
    'uz': ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
           "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"],
    'ru': ["Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
           "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"],
    'en': ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}


def _month_name(month: int, lang: str) -> str:
    return _MONTHS.get(lang, _MONTHS['en'])[month - 1]


async def _fetch_onthisday(lang: str) -> str | None:
    """
    Fetch a geographic 'On This Day' fact via Wikipedia's feed API.
    Tries the user's language first, then English.
    Returns a formatted string or None.
    """
    today = datetime.date.today()
    m, d = today.month, today.day

    # Language priority: user lang → English
    wiki_langs = [lang, 'en'] if lang != 'en' else ['en']

    async with httpx.AsyncClient(timeout=20, follow_redirects=True,
                                  headers=_WIKI_HEADERS) as client:
        for wl in wiki_langs:
            url = f"https://{wl}.wikipedia.org/api/rest_v1/feed/onthisday/events/{m}/{d}"
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning("OnThisDay %s HTTP %s", wl, resp.status_code)
                    continue

                events = resp.json().get('events', [])
                if not events:
                    continue

                # Prefer geographically relevant events
                geo = [e for e in events
                       if any(kw in e.get('text', '').lower() for kw in _GEO_KEYWORDS)]
                pool = geo if geo else events

                # Pick from top candidates, prefer varied years
                candidates = pool[:20]
                event = random.choice(candidates)

                year = event.get('year', '')
                text = event.get('text', '')
                if not text:
                    continue

                month_str = _month_name(m, lang)
                header = {
                    'uz': f"🗓 {d} {month_str}",
                    'ru': f"🗓 {d} {month_str}",
                    'en': f"🗓 {month_str} {d}",
                }.get(lang, f"🗓 {month_str} {d}")

                year_label = {
                    'uz': f"{year} yilda bu kunda:",
                    'ru': f"В этот день в {year} году:",
                    'en': f"On this day in {year}:",
                }.get(lang, f"On this day in {year}:")

                return f"{header}\n\n<i>{html.escape(year_label)}</i>\n\n{html.escape(text)}"

            except Exception as e:
                logger.warning("OnThisDay fetch failed (%s): %s", wl, e)

    return None


# ─── kept for mini-app / in-game result facts (still used in guess.py) ────────

async def _fetch_wiki_fact(country_uz: str, lang: str) -> str | None:
    """Return a Wikipedia extract for a country. Used after correct answers."""
    country_en = _UZ_TO_EN.get(country_uz, country_uz)
    title = urllib.parse.quote(country_en.replace(' ', '_'))
    langs_to_try = ['en'] if lang == 'en' else ['en', lang]

    async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                  headers=_WIKI_HEADERS) as client:
        for wiki_lang in langs_to_try:
            if wiki_lang == lang and lang != 'en':
                from translations import COUNTRY_NAMES_RU
                local_name = (COUNTRY_NAMES_RU if lang == 'ru' else COUNTRY_NAMES_EN).get(country_uz, country_en)
                local_title = urllib.parse.quote(local_name.replace(' ', '_'))
                url = f"https://{wiki_lang}.wikipedia.org/api/rest_v1/page/summary/{local_title}"
            else:
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    extract = resp.json().get('extract', '').strip()
                    if extract:
                        sentences = [s.strip() for s in extract.split('. ') if s.strip()]
                        return '. '.join(sentences[:2]) + ('.' if not sentences[0].endswith('.') else '')
            except Exception as exc:
                logger.warning("Wikipedia fact failed (%s, %s): %s", wiki_lang, country_en, exc)
    return None


async def fetch_wiki_sentences(country_uz: str, lang: str, max_sentences: int = 5) -> list[str]:
    """Return Wikipedia sentences for progressive hints in-game."""
    country_en = _UZ_TO_EN.get(country_uz, country_uz)
    title = urllib.parse.quote(country_en.replace(' ', '_'))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                      headers=_WIKI_HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                extract = resp.json().get('extract', '').strip()
                if extract:
                    sentences = [s.strip() + '.' for s in extract.split('. ') if len(s.strip()) > 20]
                    return sentences[:max_sentences]
    except Exception as exc:
        logger.warning("Wikipedia sentences failed (%s): %s", country_en, exc)
    return []


# ─── Bot commands ─────────────────────────────────────────────────────────────

async def daily_facts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle daily-facts subscription."""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or user_id
    lang = get_user_lang(user_id)
    in_group = update.effective_chat.type in ('group', 'supergroup')

    new_state = toggle_daily_facts(user_id, username)
    key = 'daily_facts_on' if new_state else 'daily_facts_off'
    await update.message.reply_text(t(lang, key), reply_markup=default_kb(lang, in_group))
    logger.info("Daily facts toggled: user=%s → %s", user_id, new_state)


async def _send_daily_fact_to(bot, user_id: str, lang: str) -> bool:
    """Fetch an 'On This Day' fact and send to user. Returns True on success."""
    fact = await _fetch_onthisday(lang)
    if not fact:
        logger.warning("No OnThisDay fact found for user=%s lang=%s", user_id, lang)
        return False

    title = {
        'uz': "🌍 <b>Bugungi geografik fakt</b>",
        'ru': "🌍 <b>Географический факт дня</b>",
        'en': "🌍 <b>Geographic Fact of the Day</b>",
    }.get(lang, "🌍 <b>Geographic Fact of the Day</b>")

    text = f"{title}\n\n{fact}"
    try:
        await bot.send_message(chat_id=int(user_id), text=text, parse_mode='HTML')
        return True
    except Exception as exc:
        logger.warning("Could not send daily fact to %s: %s", user_id, exc)
        return False


async def send_daily_facts(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job: send 'On This Day' geographic fact to every subscriber."""
    subscribers = get_daily_facts_subscribers()
    logger.info("Daily facts job: %d subscriber(s)", len(subscribers))
    if not subscribers:
        return

    ok = 0
    for user_id, lang in subscribers:
        if await _send_daily_fact_to(context.bot, user_id, lang):
            ok += 1
    logger.info("Daily facts sent: %d/%d", ok, len(subscribers))


async def test_fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/testfact — send today's fact immediately for testing."""
    user_id = str(update.effective_user.id)
    lang = get_user_lang(user_id)

    loading = {"uz": "⏳ Yuklanmoqda…", "ru": "⏳ Загрузка…", "en": "⏳ Loading…"}.get(lang, "⏳")
    await update.message.reply_text(loading)

    success = await _send_daily_fact_to(context.bot, user_id, lang)
    if not success:
        err = {"uz": "❌ Bugungi fakt yuklab bo'lmadi.",
               "ru": "❌ Не удалось загрузить факт.",
               "en": "❌ Could not load today's fact."}.get(lang, "❌")
        await update.message.reply_text(err)
    logger.info("Test fact: user=%s success=%s", user_id, success)
