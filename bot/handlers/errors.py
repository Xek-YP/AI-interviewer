import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from exceptions import (
    AlreadyAnsweredError,
    InterviewIsCompletedError,
    InterviewNotFoundOrInterraptedError,
    QuestionNotFoundError,
    LLMAuthenticationError,
    LLMInsufficientBalanceError,
    LLMServiceError,
    LLMTemporaryError,
)

router = Router()

logger = logging.getLogger(__name__)


ERROR_MESSAGES: dict[type[Exception], str] = {
    QuestionNotFoundError:
        "Вопрос не найден. Попробуйте начать собеседование заново.",

    InterviewNotFoundOrInterraptedError:
        "Собеседование не найдено или было прервано.",

    InterviewIsCompletedError:
        "Это собеседование уже завершено.",

    AlreadyAnsweredError:
        "На этот вопрос уже был получен ответ.",

    LLMTemporaryError:
        "Сервис временно недоступен. Попробуйте повторить действие позже.",

    LLMAuthenticationError:
        "Произошла техническая ошибка при обращении к AI.",

    LLMInsufficientBalanceError:
        "Сервис временно недоступен. Попробуйте позже.",

    LLMServiceError:
        "Не удалось обработать запрос. Попробуйте ещё раз.",
}


@router.error()
async def error_handler(event: ErrorEvent):
    """Централизованно обрабатывает ошибки handlers."""

    exception = event.exception
    message = event.update.message

    if message is None:
        return

    error_message = ERROR_MESSAGES.get(
        type(exception),
        "Произошла непредвиденная ошибка. Попробуйте ещё раз.",
    )

    logger.error(
        "Ошибка handler: %s | Ответ пользователю: %s",
        exception,
        error_message
    )

    if type(exception) not in ERROR_MESSAGES:
        logger.exception(
            "Необработанная ошибка в Telegram handler",
            exc_info=exception,
        )

    await message.answer(error_message)
