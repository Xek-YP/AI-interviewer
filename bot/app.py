from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import settings
from config.logging_config import setup_logging
from bot.handlers import register_handlers

async def start_bot():
    setup_logging()

    bot = Bot(token=settings.telegram_bot_token)

    dp = Dispatcher(storage=MemoryStorage())

    register_handlers(dp=dp)

    await dp.start_polling(bot)
