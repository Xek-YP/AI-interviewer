from .base import UserVisibleError


class InterviewNotFoundOrInterraptedError(UserVisibleError):
    """Ошибка собеседование не найдено или прервано."""

class InterviewIsCompletedError(UserVisibleError):
    """Ошибка собеседование закончено."""

class InvalidInterviewRequestError(UserVisibleError):
    """Ошибка подачи некорректных данных(должность/требования)."""


class InterviewLimitExceededError(UserVisibleError):
    """Превышен лимит собеседований по текущей подписке."""


class UserBlockedError(UserVisibleError):
    """Пользователь заблокирован администратором."""
