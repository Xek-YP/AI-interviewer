from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from config.settings import settings
from config.logging_config import setup_logging
from bot.handlers import register_handlers


async def start_bot() -> None:
    """Запускает Telegram-бота с FSM в Redis."""
    setup_logging()

    bot = Bot(token=settings.telegram_bot_token)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    register_handlers(dp=dp)

    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()
