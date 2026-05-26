import os
from dotenv import load_dotenv

load_dotenv()

print("DEBUG env keys:", [k for k in os.environ if 'TOKEN' in k or 'BOT' in k or 'RAILWAY' in k])

BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
WEBAPP_URL: str = os.getenv('WEBAPP_URL', '')
DB_PATH: str = os.getenv('DB_PATH', 'geography_bot.db')
SUPPORTED_LANGS: tuple = ('uz', 'ru', 'en')
API_PORT: int = int(os.getenv('API_PORT', '8080'))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set. Check your .env file.")
