from aiogram import F, Router
from aiogram.types import Message

from bot.handlers.messages import HELP_MESSAGE
from bot.keyboards.buttons_text import HELP


router = Router()


@router.message(F.text == HELP)
async def help_handler(
    message: Message,
):
    """Показывает справочную информацию."""

    await message.answer(
        HELP_MESSAGE
    )
