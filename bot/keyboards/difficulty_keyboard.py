from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.keyboards.buttons_text import JUNIOR, MIDDLE, SENIOR


def create_difficulty_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=JUNIOR),
                KeyboardButton(text=MIDDLE),
            ],
            [
                KeyboardButton(text=SENIOR)
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

