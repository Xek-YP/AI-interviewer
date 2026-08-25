from pydantic import BaseModel

from database.enums import Difficulty


class GeneratedQuestion(BaseModel):
    """Схема ответа LLM 1-го вопроса."""

    question_text: str
    category: str
    difficulty: Difficulty


class InterviewQuestionPool(BaseModel):
    """Схема генерации пула вопросов собеседования."""

    questions: list[GeneratedQuestion]
