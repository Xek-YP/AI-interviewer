from pydantic import BaseModel, Field


class InterviewEvaluation(BaseModel):
    """Схема итоговой оценки кандидата."""

    score: int = Field(ge=0, le=100)
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
    confidence: float | None = Field(ge=0, le=1)

class InterviewRequestValidation(BaseModel):
    valid: bool
    reason: str
