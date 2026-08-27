import logging

from aiogram import Bot, Router
from aiogram.types import ErrorEvent

from exceptions import UserVisibleError
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
    user_id = None

    if message and message.from_user:
        user_id = message.from_user.id

    if message:
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

    await message.answer(error_message)
