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


async def _fetch_wiki_fact(country_uz: str, lang: str) -> str | None:
    """Return a Wikipedia extract (1-2 sentences). Always tries English first for reliability."""
    country_en = _UZ_TO_EN.get(country_uz, country_uz)
    title = urllib.parse.quote(country_en.replace(' ', '_'))

    # Always try English Wikipedia (most complete); also try user's language if not English
    langs_to_try = ['en'] if lang == 'en' else ['en', lang]

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for wiki_lang in langs_to_try:
            if wiki_lang == lang and lang != 'en':
                # For non-English, use the localised title from COUNTRY_NAMES_RU/EN if available
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
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
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
    await update.message.reply_text(t(lang, key), reply_markup=default_kb(lang))
    logger.info("Daily facts toggled: user=%s → %s", user_id, new_state)


async def send_daily_facts(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job: send one random geography fact to every subscriber."""
    subscribers = get_daily_facts_subscribers()
    if not subscribers:
        return

    country_uz = random.choice(COUNTRIES)

    for user_id, lang in subscribers:
        country_display = html.escape(get_country_name(country_uz, lang))
        fact = await _fetch_wiki_fact(country_uz, lang)
        if not fact:
            logger.warning("No fact for %s, skipping user %s", country_uz, user_id)
            continue
        text = t(lang, 'daily_fact', country=country_display, fact=html.escape(fact))
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode='HTML',
            )
        except Exception as exc:
            logger.warning("Could not send daily fact to %s: %s", user_id, exc)
