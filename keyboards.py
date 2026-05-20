import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from translations import t
from config import WEBAPP_URL


def default_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, 'btn_country'), t(lang, 'btn_capital')],
            [t(lang, 'btn_top'), t(lang, 'btn_stats'), t(lang, 'btn_reset'), t(lang, 'btn_help')],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def guess_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, 'btn_hint'), t(lang, 'btn_capital')],
            [t(lang, 'btn_reset'), t(lang, 'btn_help')],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def map_kb(lang: str) -> ReplyKeyboardMarkup:
    if not WEBAPP_URL or WEBAPP_URL == 'https://your-domain.com/map.html':
        return guess_kb(lang)
    return ReplyKeyboardMarkup(
        [
            [telegram.KeyboardButton(t(lang, 'btn_map'), web_app=WebAppInfo(url=WEBAPP_URL))],
            [t(lang, 'btn_hint'), t(lang, 'btn_reset')],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# Inline keyboard shown during onboarding (/start for new users)
ONBOARD_LANG_KB = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🇺🇿 O'zbek",   callback_data='onboard_uz'),
        InlineKeyboardButton("🇷🇺 Русский",  callback_data='onboard_ru'),
        InlineKeyboardButton("🇬🇧 English",  callback_data='onboard_en'),
    ]
])

# Inline keyboard shown by /language command (for returning users)
CHANGE_LANG_KB = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🇺🇿 O'zbek",   callback_data='lang_uz'),
        InlineKeyboardButton("🇷🇺 Русский",  callback_data='lang_ru'),
        InlineKeyboardButton("🇬🇧 English",  callback_data='lang_en'),
    ]
])
