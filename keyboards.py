import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from translations import t
from config import WEBAPP_URL


def default_kb(lang: str) -> ReplyKeyboardMarkup:
    rows = [
        [t(lang, 'btn_country'), t(lang, 'btn_capital'), t(lang, 'btn_flag')],
        [t(lang, 'btn_currency'), t(lang, 'btn_challenge'), t(lang, 'btn_stats')],
        [t(lang, 'btn_top'), t(lang, 'btn_region'), t(lang, 'btn_difficulty')],
        [t(lang, 'btn_daily_facts'), t(lang, 'btn_info'), t(lang, 'btn_reset')],
        [t(lang, 'btn_help')],
    ]
    if WEBAPP_URL:
        rows.append([telegram.KeyboardButton(t(lang, 'btn_miniapp'), web_app=WebAppInfo(url=WEBAPP_URL))])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


def guess_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [t(lang, 'btn_hint'), t(lang, 'btn_reset')],
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


def continent_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(lang, 'region_africa'),       callback_data='region_africa'),
            InlineKeyboardButton(t(lang, 'region_asia'),         callback_data='region_asia'),
            InlineKeyboardButton(t(lang, 'region_europe'),       callback_data='region_europe'),
        ],
        [
            InlineKeyboardButton(t(lang, 'region_north_america'), callback_data='region_north_america'),
            InlineKeyboardButton(t(lang, 'region_south_america'), callback_data='region_south_america'),
            InlineKeyboardButton(t(lang, 'region_oceania'),       callback_data='region_oceania'),
        ],
        [
            InlineKeyboardButton(t(lang, 'region_all'), callback_data='region_all'),
        ],
    ])


def difficulty_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, 'difficulty_easy'),   callback_data='diff_easy')],
        [InlineKeyboardButton(t(lang, 'difficulty_normal'), callback_data='diff_normal')],
        [InlineKeyboardButton(t(lang, 'difficulty_hard'),   callback_data='diff_hard')],
    ])
