class AlreadyAnsweredError(Exception):
    """Ошибка повторного ответа на 1 и тот же вопрос."""


class NoAnswerError(Exception):
    """Нет ответов на собеседование."""