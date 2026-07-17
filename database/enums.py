from enum import StrEnum

class Difficulty(StrEnum):
    """Сложность собеседования."""

    JUNIOR = 'JUNIOR'
    MIDDLE = 'MIDDLE'
    SENIOR = 'SENIOR'

class InterviewStatus(StrEnum):
    """Статус собеседования."""

    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    INTERRUPTED = 'INTERRUPTED'
