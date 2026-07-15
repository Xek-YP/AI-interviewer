from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import bot.handlers.messages as handlers_text
from bot.keyboards.main_keyboard import create_main_keyboard
from database.session import AsyncSessionLocal
from services.user_service import UserService

router = Router()

MAIN_KEYBOARD = create_main_keyboard()

@router.message(CommandStart())
async def start_handler(message: Message):
    if message.from_user is None:
        return
    async with AsyncSessionLocal() as async_session:
        user_service = UserService()
        user = await user_service.register_user(
            session=async_session,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )
    await message.answer(
        handlers_text.WELCOME_MESSAGE.format(first_name=user.first_name),
        reply_markup=MAIN_KEYBOARD,
    )
