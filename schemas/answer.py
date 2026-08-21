from dataclasses import dataclass
from pydantic import BaseModel, Field

from database.enums import Difficulty
from database.models import InterviewQuestion, UserAnswer

class AnswerEvaluation(BaseModel):
    """Схема ответа LLM."""

    score: int = Field(ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    recommended_difficulty: Difficulty
    confidence: float | None = Field(default=None,ge=0,le=1)

@dataclass
class SubmitAnswerResult:
    next_question: InterviewQuestion | None
    user_answer: UserAnswer
    interview_score: int | None
