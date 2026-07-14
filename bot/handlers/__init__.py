from aiogram import Dispatcher

from bot.handlers.start import router as start_router

def register_handlers(dp: Dispatcher) -> None:
    """Регистрирует все роутеры приложения"""
    dp.include_router(start_router)
