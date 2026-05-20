import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
WEBAPP_URL: str = os.getenv('WEBAPP_URL', '')
DB_PATH: str = 'geography_bot.db'
SUPPORTED_LANGS: tuple = ('uz', 'ru', 'en')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set. Check your .env file.")
