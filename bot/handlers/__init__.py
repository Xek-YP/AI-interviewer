from aiogram import Dispatcher

from bot.handlers.start import router as start_router
from bot.handlers.interview import router as interview_router
from bot.handlers.errors import router as error_router

def register_handlers(dp: Dispatcher) -> None:
    """Регистрирует все роутеры приложения"""
    dp.include_router(start_router)
    dp.include_router(interview_router)
    dp.include_router(error_router)
