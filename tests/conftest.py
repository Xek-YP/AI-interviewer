import inspect
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

# Settings загружается при импорте модулей приложения — задаём env заранее.
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-bot-token")
os.environ.setdefault("ADMIN_TELEGRAM_ID", "1")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-deepseek-key")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")

from database.enums import Difficulty, InterviewStatus  # noqa: E402
from database.models import Interview, InterviewQuestion, User, UserAnswer  # noqa: E402
from schemas.answer import AnswerEvaluation  # noqa: E402
from schemas.interview import InterviewEvaluation, InterviewRequestValidation  # noqa: E402
from schemas.interview_question import GeneratedQuestion, InterviewQuestionPool  # noqa: E402


@pytest.fixture
def session():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def user():
    return User(
        id=1,
        telegram_id=12345,
        first_name="Ivan",
        username="ivan",
    )


@pytest.fixture
def interview():
    inv = MagicMock(spec=Interview)
    inv.id = 10
    inv.user_id = 1
    inv.status = InterviewStatus.IN_PROGRESS
    inv.position = "Python Backend"
    inv.requirements = "FastAPI, PostgreSQL"
    inv.difficulty = Difficulty.MIDDLE
    inv.question_count = 5
    inv.score = None
    inv.summary = None
    inv.strengths = None
    inv.weaknesses = None
    inv.recommendation = None
    inv.completed_at = None
    return inv


@pytest.fixture
def question(interview):
    q = MagicMock(spec=InterviewQuestion)
    q.id = 100
    q.interview_id = interview.id
    q.question_text = "Что такое GIL?"
    q.difficulty = Difficulty.MIDDLE
    q.category = "Python"
    q.order_number = 1
    return q


@pytest.fixture
def user_answer(question):
    answer = MagicMock(spec=UserAnswer)
    answer.id = 50
    answer.interview_question_id = question.id
    answer.answer_text = "GIL — глобальная блокировка интерпретатора"
    answer.score = 80
    answer.strengths = "• Структура"
    answer.weaknesses = "• Мало примеров"
    answer.confidence = 0.9
    answer.question = question
    return answer


@pytest.fixture
def answer_evaluation():
    return AnswerEvaluation(
        score=80,
        strengths=["Структура"],
        weaknesses=["Мало примеров"],
        confidence=0.9,
    )


@pytest.fixture
def interview_evaluation():
    return InterviewEvaluation(
        score=75,
        summary="Хороший кандидат",
        strengths=["База Python"],
        weaknesses=["Опыт с БД"],
        recommendation="hire",
        confidence=0.85,
    )


@pytest.fixture
def valid_validation():
    return InterviewRequestValidation(valid=True, reason="ok")


@pytest.fixture
def invalid_validation():
    return InterviewRequestValidation(valid=False, reason="Не вакансия")


@pytest.fixture
def question_pool():
    return InterviewQuestionPool(
        questions=[
            GeneratedQuestion(
                question_text=f"Вопрос {i}",
                category="Python",
                difficulty=Difficulty.MIDDLE,
            )
            for i in range(1, 6)
        ]
    )
