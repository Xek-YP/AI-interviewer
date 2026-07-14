from aiogram import Bot, Dispatcher

from config.settings import settings
from bot.handlers import register_handlers

async def start_bot():
    bot = Bot(token=settings.telegram_bot_token)

    dp = Dispatcher()

    register_handlers(dp=dp)

    await dp.start_polling(bot)