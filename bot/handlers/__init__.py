from aiogram import Dispatcher

from bot.handlers.start import router as start_router
from bot.handlers.interview_setup import router as interview_setup_router
from bot.handlers.interview import router as interview_router
from bot.handlers.history import router as history_router
from bot.handlers.profile import router as profile_router
from bot.handlers.help import router as help_router
from bot.handlers.errors import router as error_router

def register_handlers(dp: Dispatcher) -> None:
    """Регистрирует все роутеры приложения"""
    dp.include_router(start_router)
    dp.include_router(interview_setup_router)
    dp.include_router(interview_router)
    dp.include_router(history_router)
    dp.include_router(profile_router)
    dp.include_router(help_router)
    dp.include_router(error_router)
