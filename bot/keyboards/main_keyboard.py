from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import bot.keyboards.buttons_text as text


def create_main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает главную клавиатуру."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=text.START_INTERVIEW),
                KeyboardButton(text=text.VIEW_HISTORY),
            ],
            [
                KeyboardButton(text=text.PROFILE),
                KeyboardButton(text=text.BUY_PREMIUM),
            ],
            [
                KeyboardButton(text=text.HELP),
            ],
        ],
        resize_keyboard=True,
    )
