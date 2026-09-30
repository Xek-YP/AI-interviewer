from .base import UserVisibleError


class LlmBudgetExceededError(UserVisibleError):
    """Дневной лимит запросов к LLM исчерпан."""

    def __init__(self, message: str, notify_admin: bool = False):
        super().__init__(message)
        self.notify_admin = notify_admin


class LLMServiceError(Exception):
    """Базовая ошибка LLM-сервиса."""


class LLMTemporaryError(LLMServiceError):
    """Временная ошибка LLM-провайдера."""


class LLMAuthenticationError(LLMServiceError):
    """Ошибка аутентификации в LLM-провайдере."""


class LLMInsufficientBalanceError(LLMServiceError):
    """Недостаточно средств у LLM-провайдера."""
