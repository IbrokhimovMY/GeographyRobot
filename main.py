import logging

import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN
from database import init_db
from handlers.onboarding import build_onboarding_handler
from handlers.game import get_country, get_capital, hint
from handlers.guess import handle_guess, handle_webapp_data
from handlers.misc import (
    stats, top, reset, help_command,
    language_command, language_callback,
)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(),
    ],
)


def main() -> None:
    init_db()
    logging.getLogger(__name__).info("Bot starting…")

    app = Application.builder().token(BOT_TOKEN).build()

    # Onboarding must be first so ConversationHandler intercepts /start and
    # the name-entry message before the generic MessageHandler sees them.
    app.add_handler(build_onboarding_handler())

    # Regular commands
    app.add_handler(CommandHandler('language',   language_command))
    app.add_handler(CommandHandler('getcountry', get_country))
    app.add_handler(CommandHandler('getcapital', get_capital))
    app.add_handler(CommandHandler('hint',       hint))
    app.add_handler(CommandHandler('stats',      stats))
    app.add_handler(CommandHandler('top',        top))
    app.add_handler(CommandHandler('reset',      reset))
    app.add_handler(CommandHandler('help',       help_command))

    # Inline keyboard callback for /language (returning users)
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r'^lang_'))

    # Free-text guesses and map WebApp
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    app.run_polling(allowed_updates=telegram.Update.ALL_TYPES)


if __name__ == '__main__':
    main()
