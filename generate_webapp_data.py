"""Run once to generate webapp/data.js from the Python country data."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data import (COUNTRIES, COUNTRIES_CAPITALS, COUNTRY_FLAGS, COUNTRY_CONTINENTS,
                  COUNTRY_HINTS_UZ, COUNTRY_ISO2, COUNTRY_CURRENCIES)
from translations import COUNTRY_NAMES_EN, COUNTRY_NAMES_RU, COUNTRY_HINTS_EN, COUNTRY_HINTS_RU

game_data = []
for uz in COUNTRIES:
    cur = COUNTRY_CURRENCIES.get(uz, ("", ""))
    game_data.append({
        "key": uz,
        "names": {
            "uz": uz,
            "en": COUNTRY_NAMES_EN.get(uz, uz),
            "ru": COUNTRY_NAMES_RU.get(uz, uz),
        },
        "capital": COUNTRIES_CAPITALS.get(uz, ""),
        "flag": COUNTRY_FLAGS.get(uz, "🏴"),
        "continent": COUNTRY_CONTINENTS.get(uz, ""),
        "iso2": COUNTRY_ISO2.get(uz, ""),
        "currency": {"name": cur[0], "code": cur[1]},
        "hints": {
            "uz": COUNTRY_HINTS_UZ.get(uz, ""),
            "en": COUNTRY_HINTS_EN.get(uz, ""),
            "ru": COUNTRY_HINTS_RU.get(uz, ""),
        },
    })

os.makedirs("webapp", exist_ok=True)
out = f"const GAME_DATA = {json.dumps(game_data, ensure_ascii=False)};\n"
with open("webapp/data.js", "w", encoding="utf-8") as f:
    f.write(out)

print(f"✅ Generated webapp/data.js  ({len(game_data)} countries, {len(out)//1024}KB)")
