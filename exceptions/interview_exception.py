from .base import UserVisibleError


class InterviewNotFoundOrInterraptedError(UserVisibleError):
    """Ошибка собеседование не найдено или прервано."""

class InterviewIsCompletedError(UserVisibleError):
    """Ошибка собеседование закончено."""

class InvalidInterviewRequestError(UserVisibleError):
    """Ошибка подачи некорректных данных(должность/требования)."""
