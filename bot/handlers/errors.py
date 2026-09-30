import logging

from aiogram import Bot, Router
from aiogram.types import ErrorEvent

from bot.keyboards.payment_keyboard import create_buy_premium_keyboard
from exceptions import (
    InterviewLimitExceededError,
    LlmBudgetExceededError,
    UserVisibleError,
)
from services.notification_service import notification_service

router = Router()

logger = logging.getLogger(__name__)


@router.error()
async def error_handler(
    event: ErrorEvent,
    bot: Bot
):
    """Централизованно обрабатывает ошибки handlers."""

    exception = event.exception
    message = event.update.message
    callback = event.update.callback_query
    user_id = None

    if message and message.from_user:
        user_id = message.from_user.id
    elif callback and callback.from_user:
        user_id = callback.from_user.id

    if isinstance(exception, LlmBudgetExceededError):
        if exception.notify_admin:
            try:
                await notification_service.send_error(
                    bot=bot,
                    exception=exception,
                    user_id=user_id,
                )
            except Exception:
                logger.exception(
                    'Не удалось уведомить администратора о лимите LLM'
                )
        error_message = str(exception)
        if message:
            await message.answer(error_message)
        elif callback:
            try:
                await callback.answer(error_message, show_alert=True)
            except Exception:
                if callback.message:
                    await callback.message.answer(error_message)
        return

    if isinstance(exception, InterviewLimitExceededError):
        text = str(exception)
        markup = create_buy_premium_keyboard()
        if message:
            await message.answer(text, reply_markup=markup)
        elif callback and callback.message:
            await callback.message.answer(text, reply_markup=markup)
            await callback.answer()
        return

    if isinstance(exception, UserVisibleError):
        error_message = str(exception)
    else:
        error_message = (
            'Извините, произошла ошибка по нашей вине. '
            'Мы уже работаем над исправлением.'
        )
        logger.exception(
            'Ошибка handler: %s',
            exception
        )
        await notification_service.send_error(
            bot=bot,
            exception=exception,
            user_id=user_id
        )

    if message:
        await message.answer(error_message)
        return

    if callback:
        try:
            await callback.answer(error_message, show_alert=True)
        except Exception:
            if callback.message:
                await callback.message.answer(error_message)
        return
