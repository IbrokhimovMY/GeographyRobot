"""Daily geography facts: per-user toggle and scheduled delivery via Wikipedia API."""
import html
import logging
import random
import urllib.parse

import httpx
from telegram.ext import ContextTypes

from data import COUNTRIES, MAP_EN_TO_UZ
from database import get_daily_facts_subscribers, toggle_daily_facts, get_user_lang
from keyboards import default_kb
from translations import t, get_country_name, COUNTRY_NAMES_EN

from telegram import Update

logger = logging.getLogger(__name__)

_UZ_TO_EN: dict[str, str] = {uz: en for en, uz in MAP_EN_TO_UZ.items()}
_UZ_TO_EN.update(COUNTRY_NAMES_EN)


# Wikipedia requires a descriptive User-Agent — cloud IPs are blocked without it
_WIKI_HEADERS = {
    "User-Agent": "MYGeoRobot/1.0 (Geography quiz Telegram bot; ibrokhimovmy@gmail.com)",
    "Accept": "application/json",
}


async def _fetch_wiki_fact(country_uz: str, lang: str) -> str | None:
    """Return a Wikipedia extract (1-2 sentences)."""
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
                logger.warning("Wikipedia fetch failed (%s, %s): %s", wiki_lang, country_en, exc)
    return None


async def fetch_wiki_sentences(country_uz: str, lang: str, max_sentences: int = 5) -> list[str]:
    """Return up to max_sentences Wikipedia sentences for progressive hints."""
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
        logger.warning("Wikipedia sentences fetch failed (%s): %s", country_en, exc)
    return []


async def daily_facts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or user_id
    lang = get_user_lang(user_id)

    new_state = toggle_daily_facts(user_id, username)
    key = 'daily_facts_on' if new_state else 'daily_facts_off'
    in_group = update.effective_chat.type in ('group', 'supergroup')
    await update.message.reply_text(t(lang, key), reply_markup=default_kb(lang, in_group))
    logger.info("Daily facts toggled: user=%s → %s", user_id, new_state)


async def _send_fact_to_user(bot, user_id: str, lang: str) -> bool:
    """Pick a random country, fetch fact, send to user. Returns True on success."""
    country_uz = random.choice(COUNTRIES)
    country_display = html.escape(get_country_name(country_uz, lang))

    fact = await _fetch_wiki_fact(country_uz, lang)
    if not fact:
        # Try a different country if first fails
        for _ in range(3):
            country_uz = random.choice(COUNTRIES)
            fact = await _fetch_wiki_fact(country_uz, lang)
            if fact:
                country_display = html.escape(get_country_name(country_uz, lang))
                break

    if not fact:
        logger.warning("Wikipedia fact fetch failed for user=%s (tried 4 countries)", user_id)
        return False

    text = t(lang, 'daily_fact', country=country_display, fact=html.escape(fact))
    try:
        await bot.send_message(chat_id=int(user_id), text=text, parse_mode='HTML')
        return True
    except Exception as exc:
        logger.warning("Could not send daily fact to %s: %s", user_id, exc)
        return False


async def send_daily_facts(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job: send geography fact to every subscriber."""
    subscribers = get_daily_facts_subscribers()
    logger.info("Daily facts job: %d subscriber(s)", len(subscribers))
    if not subscribers:
        return

    ok = 0
    for user_id, lang in subscribers:
        if await _send_fact_to_user(context.bot, user_id, lang):
            ok += 1
    logger.info("Daily facts sent: %d/%d", ok, len(subscribers))


async def test_fact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a test fact to the caller right now (no need to wait until 9 AM)."""
    user_id = str(update.effective_user.id)
    lang = get_user_lang(user_id)
    await update.message.reply_text("⏳ Fakt yuklanmoqda…" if lang == 'uz'
                                    else "⏳ Loading fact…")
    success = await _send_fact_to_user(context.bot, user_id, lang)
    if not success:
        err = {"uz": "❌ Fakt yuklab bo'lmadi. Wikipedia API javob bermadi.",
               "ru": "❌ Не удалось загрузить факт.",
               "en": "❌ Could not load fact. Wikipedia API unavailable."}.get(lang, "❌")
        await update.message.reply_text(err)
    logger.info("Test fact: user=%s success=%s", user_id, success)
