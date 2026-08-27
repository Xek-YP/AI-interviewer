from .base import UserVisibleError


class AlreadyAnsweredError(UserVisibleError):
    """Ошибка повторного ответа на 1 и тот же вопрос."""


class NoAnswerError(UserVisibleError):
    """Нет ответов на собеседование."""
