from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.buttons_text import BUY_PREMIUM_CALLBACK


def create_buy_premium_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопка покупки PREMIUM."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Оплатить PREMIUM',
                    callback_data=BUY_PREMIUM_CALLBACK,
                )
            ]
        ]
    )
