from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.keyboards.buttons_text import END_INTERVIEW


def create_interview_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура во время прохождения собеседования."""

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=END_INTERVIEW),
            ],
        ],
        resize_keyboard=True
    )