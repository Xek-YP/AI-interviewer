from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.session import AsyncSessionLocal
from services.user_service import UserService

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    async with AsyncSessionLocal() as async_session:
        user_service = UserService()
        if message.from_user is None:
            return
        user = await user_service.register_user(
            session=async_session,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )
    await message.answer(f'Привет, {user.first_name}!')
