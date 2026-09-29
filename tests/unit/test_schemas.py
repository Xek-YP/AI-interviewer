import pytest
from pydantic import ValidationError

from database.enums import Difficulty
from schemas.answer import AnswerEvaluation
from schemas.interview import InterviewEvaluation, InterviewRequestValidation
from schemas.interview_question import GeneratedQuestion, InterviewQuestionPool


def test_answer_evaluation_valid():
    """Валидная схема оценки ответа принимает корректные данные."""
    evaluation = AnswerEvaluation(
        score=50,
        strengths=["a"],
        weaknesses=["b"],
    )
    assert evaluation.score == 50
    assert evaluation.confidence is None


@pytest.mark.parametrize("score", [-1, 101])
def test_answer_evaluation_score_bounds(score):
    """Оценка ответа отклоняет score вне диапазона 0–100."""
    with pytest.raises(ValidationError):
        AnswerEvaluation(score=score, strengths=[], weaknesses=[])


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_answer_evaluation_confidence_bounds(confidence):
    """Оценка ответа отклоняет confidence вне диапазона 0–1."""
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            score=10,
            strengths=[],
            weaknesses=[],
            confidence=confidence,
        )


def test_interview_evaluation_valid():
    """Валидная итоговая оценка собеседования принимается схемой."""
    evaluation = InterviewEvaluation(
        score=75,
        summary="ok",
        strengths=["a"],
        weaknesses=["b"],
        recommendation="hire",
        confidence=0.5,
    )
    assert evaluation.recommendation == "hire"


def test_interview_evaluation_score_bounds():
    """Итоговая оценка отклоняет score больше 100."""
    with pytest.raises(ValidationError):
        InterviewEvaluation(
            score=150,
            summary="ok",
            strengths=[],
            weaknesses=[],
            recommendation="no",
            confidence=None,
        )


def test_interview_request_validation():
    """Схема валидации вакансии принимает boolean и reason."""
    validation = InterviewRequestValidation(valid=True, reason="ok")
    assert validation.valid is True


def test_interview_question_pool():
    """Пул вопросов принимает список GeneratedQuestion."""
    pool = InterviewQuestionPool(
        questions=[
            GeneratedQuestion(
                question_text="Q",
                category="DB",
                difficulty=Difficulty.SENIOR,
            )
        ]
    )
    assert len(pool.questions) == 1
    assert pool.questions[0].difficulty == Difficulty.SENIOR


def test_generated_question_rejects_invalid_difficulty():
    """Сгенерированный вопрос отклоняет неизвестный уровень сложности."""
    with pytest.raises(ValidationError):
        GeneratedQuestion(
            question_text="Q",
            category="DB",
            difficulty="INTERN",
        )
