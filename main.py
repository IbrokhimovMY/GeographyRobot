import logging
from datetime import time, timezone, timedelta

import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PollAnswerHandler, TypeHandler, filters

from config import BOT_TOKEN, API_PORT
from database import init_db
from api_server import start_api_server
from handlers.onboarding import build_onboarding_handler
from handlers.game import get_country, get_capital, hint
from handlers.guess import handle_guess, handle_webapp_data
from handlers.misc import (
    stats, top, reset, help_command,
    language_command, language_callback, users_command, admin_command,
)
from handlers.facts import daily_facts_command, send_daily_facts, test_fact_command
from handlers.flag import get_flag
from handlers.info import info_command
from handlers.challenge import get_challenge
from handlers.currency import get_currency_game
from handlers.quiz import (
    start_variant_quiz, start_text_quiz, stop_quiz,
    handle_variant_callback, handle_quiz_diff_callback,
)
from handlers.poll_quiz import handle_poll_answer
from handlers.invite import invite_command
from handlers.user_quiz import (
    build_addquestion_handler, myquestions_command, myquestions_delete,
)
from handlers.broadcast import broadcast_start, broadcast_cancel, broadcast_handle
from handlers.settings import (
    region_command, region_callback,
    difficulty_command, difficulty_callback,
)
from handlers.subscription import subscription_middleware

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(),
    ],
)


async def _post_init(application) -> None:
    await start_api_server(port=API_PORT)
    await _set_commands(application.bot)


_BOT_COMMANDS = {
    'uz': [
        ('start',         "Botni boshlash"),
        ('addquestion',   "📝 Savol qo'shish"),
        ('myquestions',   "📋 Mening savollarim"),
        ('stopquiz',      "⏹ Quizni to'xtatish"),
        ('admin',         "👨‍💼 Admin bilan bog'lanish"),
    ],
    'ru': [
        ('start',         "Запустить бота"),
        ('addquestion',   "📝 Добавить вопрос"),
        ('myquestions',   "📋 Мои вопросы"),
        ('stopquiz',      "⏹ Остановить квиз"),
        ('admin',         "👨‍💼 Связаться с Admin"),
    ],
    'en': [
        ('start',         "Start the bot"),
        ('addquestion',   "📝 Add a question"),
        ('myquestions',   "📋 My questions"),
        ('stopquiz',      "⏹ Stop quiz"),
        ('admin',         "👨‍💼 Contact Admin"),
    ],
}


async def set_user_commands(bot, user_id: int, lang: str) -> None:
    """Set command menu for a specific user based on their chosen bot language."""
    from telegram import BotCommand, BotCommandScopeChat
    pairs = _BOT_COMMANDS.get(lang, _BOT_COMMANDS['uz'])
    cmds = [BotCommand(cmd, desc) for cmd, desc in pairs]
    try:
        await bot.set_my_commands(cmds, scope=BotCommandScopeChat(chat_id=user_id))
    except Exception as e:
        logging.getLogger(__name__).debug("set_user_commands failed uid=%s: %s", user_id, e)


async def _set_commands(bot) -> None:
    """Remove global default commands (each user gets their own via set_user_commands)."""
    try:
        from telegram import BotCommandScopeDefault
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
    except Exception as e:
        logging.getLogger(__name__).debug("delete_my_commands: %s", e)


def main() -> None:
    init_db()
    logging.getLogger(__name__).info("Bot starting…")

    app = (Application.builder()
           .token(BOT_TOKEN)
           .concurrent_updates(True)   # handle multiple users simultaneously
           .post_init(_post_init)
           .build())

    # Subscription check runs before all other handlers (group=-1)
    app.add_handler(TypeHandler(telegram.Update, subscription_middleware), group=-1)

    # Onboarding must be first
    app.add_handler(build_onboarding_handler())
    app.add_handler(build_addquestion_handler())
    app.add_handler(CommandHandler('broadcast', broadcast_start))
    app.add_handler(CommandHandler('cancel',    broadcast_cancel))

    async def _media_broadcast(update, context):
        await broadcast_handle(update, context)
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO) & ~filters.COMMAND,
        _media_broadcast,
    ))

    # Game commands
    app.add_handler(CommandHandler('language',   language_command))
    app.add_handler(CommandHandler('getcountry', get_country))
    app.add_handler(CommandHandler('getcapital', get_capital))
    app.add_handler(CommandHandler('getflag',    get_flag))
    app.add_handler(CommandHandler('challenge',  get_challenge))
    app.add_handler(CommandHandler('getcurrency', get_currency_game))
    app.add_handler(CommandHandler('hint',       hint))
    app.add_handler(CommandHandler('info',       info_command))
    app.add_handler(CommandHandler('quiz1',      start_variant_quiz))
    app.add_handler(CommandHandler('quiz2',      start_text_quiz))
    app.add_handler(CommandHandler('stopquiz',   stop_quiz))
    app.add_handler(CommandHandler('invite',     invite_command))
    app.add_handler(CommandHandler('users',      users_command))
    app.add_handler(CommandHandler('admin',      admin_command))
    app.add_handler(CommandHandler('myquestions', myquestions_command))
    app.add_handler(CallbackQueryHandler(myquestions_delete, pattern=r'^aq_del:'))

    # Utility commands
    app.add_handler(CommandHandler('stats',      stats))
    app.add_handler(CommandHandler('top',        top))
    app.add_handler(CommandHandler('reset',      reset))
    app.add_handler(CommandHandler('help',       help_command))
    app.add_handler(CommandHandler('region',     region_command))
    app.add_handler(CommandHandler('difficulty', difficulty_command))
    app.add_handler(CommandHandler('dailyfacts', daily_facts_command))
    app.add_handler(CommandHandler('testfact',   test_fact_command))

    # Inline keyboard callbacks
    app.add_handler(CallbackQueryHandler(language_callback,    pattern=r'^lang_'))
    app.add_handler(CallbackQueryHandler(region_callback,      pattern=r'^region_'))
    app.add_handler(CallbackQueryHandler(difficulty_callback,  pattern=r'^diff_'))
    app.add_handler(CallbackQueryHandler(handle_variant_callback,   pattern=r'^vq:'))
    app.add_handler(CallbackQueryHandler(handle_quiz_diff_callback, pattern=r'^q[12]:'))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    # Free-text guesses and map WebApp
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    # Scheduled jobs — 9:00 AM Uzbekistan time (UTC+5)
    UZT = timezone(timedelta(hours=5))
    app.job_queue.run_daily(send_daily_facts, time=time(hour=9, minute=0, tzinfo=UZT))

    app.run_polling(allowed_updates=telegram.Update.ALL_TYPES)


if __name__ == '__main__':
    main()
