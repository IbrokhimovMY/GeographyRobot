"""Country info lookup: user types a country name and gets capital, continent, Wikipedia fact."""
import html
import logging

from telegram import Update
from telegram.ext import ContextTypes

from data import MAP_ANY_TO_UZ, COUNTRY_FLAGS, COUNTRY_CONTINENTS, COUNTRIES_CAPITALS
from database import get_user_lang
from keyboards import default_kb
from translations import t, get_country_name
from handlers.facts import _fetch_wiki_fact

logger = logging.getLogger(__name__)

_CONTINENT_KEY = {
    'africa': 'region_africa', 'asia': 'region_asia', 'europe': 'region_europe',
    'north_america': 'region_north_america', 'south_america': 'region_south_america',
    'oceania': 'region_oceania',
}


def _uid(update: Update) -> str:
    return str(update.effective_user.id)


def _lang(update: Update) -> str:
    return get_user_lang(_uid(update))


async def info_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(update)
    text = update.message.text.strip()

    country_uz = MAP_ANY_TO_UZ.get(text.lower())
    if not country_uz:
        await update.message.reply_text(t(lang, 'info_not_found'), reply_markup=default_kb(lang))
        return

    flag = COUNTRY_FLAGS.get(country_uz, '🏴')
    capital = COUNTRIES_CAPITALS.get(country_uz, '—')
    continent_key = COUNTRY_CONTINENTS.get(country_uz, '')
    continent_label = t(lang, _CONTINENT_KEY.get(continent_key, 'region_all'))
    country_display = html.escape(get_country_name(country_uz, lang))

    fact = await _fetch_wiki_fact(country_uz, lang)
    if fact:
        msg = t(lang, 'info_result',
                flag=flag, country=country_display,
                capital=html.escape(capital),
                continent=continent_label,
                fact=html.escape(fact))
    else:
        msg = t(lang, 'info_no_fact',
                flag=flag, country=country_display,
                capital=html.escape(capital),
                continent=continent_label)

    context.user_data.pop('awaiting_info', None)
    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=default_kb(lang))


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called when user presses the Info button — ask them to type a country name."""
    lang = _lang(update)
    context.user_data['awaiting_info'] = True
    await update.message.reply_text(t(lang, 'info_ask'), reply_markup=default_kb(lang))
