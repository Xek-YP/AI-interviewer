from dataclasses import dataclass
from pydantic import BaseModel, Field

from database.models import InterviewQuestion, UserAnswer
from .interview import InterviewEvaluation


class AnswerEvaluation(BaseModel):
    """Схема ответа LLM."""

    score: int = Field(ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    confidence: float | None = Field(default=None,ge=0,le=1)

@dataclass
class SubmitAnswerResult:
    next_question: InterviewQuestion | None
    user_answer: UserAnswer
    evaluation: InterviewEvaluation | None
