from enum import StrEnum

class Difficulty(StrEnum):
    """Сложность собеседования."""

    JUNIOR = 'Junior'
    MIDDLE = 'Middle'
    SENIOR = 'Senior'

class InterviewStatus(StrEnum):
    """Статус собеседования."""

    IN_PROGRESS = 'В процессе'
    COMPLETED = 'Завершено'
    INTERRUPTED = 'Прервано'

