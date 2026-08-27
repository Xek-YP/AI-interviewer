class LLMServiceError(Exception):
    """Базовая ошибка LLM-сервиса."""


class LLMTemporaryError(LLMServiceError):
    """Временная ошибка LLM-провайдера."""


class LLMAuthenticationError(LLMServiceError):
    """Ошибка аутентификации в LLM-провайдере."""


class LLMInsufficientBalanceError(LLMServiceError):
    """Недостаточно средств у LLM-провайдера."""
