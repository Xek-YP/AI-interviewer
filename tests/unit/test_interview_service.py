from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.enums import Difficulty, InterviewStatus
from exceptions import (
    AlreadyAnsweredError,
    InterviewIsCompletedError,
    InterviewNotFoundOrInterraptedError,
    InvalidInterviewRequestError,
    LLMServiceError,
    NoAnswerError,
    QuestionNotFoundError,
)
from services.interview_service import InterviewService


@pytest.fixture
def service():
    return InterviewService()


def test_format_evaluation_items(service):
    """Форматирование списка оценок в маркированный текст."""
    assert service._format_evaluation_items(["a", "b"]) == "• a\n• b"


def test_format_evaluation_items_empty(service):
    """Пустой список оценок форматируется в пустую строку."""
    assert service._format_evaluation_items([]) == ""


def test_calculate_interview_score_empty(service):
    """Итоговая оценка без ответов равна нулю."""
    assert service._calculate_interview_score([]) == 0


def test_calculate_interview_score_rounds_average(service):
    """Итоговая оценка считается как округлённое среднее баллов."""
    answers = [MagicMock(score=80), MagicMock(score=90), MagicMock(score=70)]
    assert service._calculate_interview_score(answers) == 80


def test_format_answers_for_evaluation(service, user_answer):
    """Ответы кандидата собираются в текст для итоговой оценки LLM."""
    user_answer.question.question_text = "Что такое GIL?"
    user_answer.answer_text = "Блокировка"
    user_answer.score = 70
    user_answer.strengths = "• ok"
    user_answer.weaknesses = "• weak"

    text = service._format_answers_for_evaluation([user_answer])

    assert "Вопрос 1:" in text
    assert "Что такое GIL?" in text
    assert "Блокировка" in text
    assert "70" in text


@pytest.mark.asyncio
async def test_get_statistics_empty(service, session):
    """Статистика без истории возвращает нулевые значения."""
    with patch.object(service, "get_history", AsyncMock(return_value=[])):
        assert await service.get_statistics(session, 1) == {
            "completed_count": 0,
            "average_score": 0,
            "best_score": 0,
        }


@pytest.mark.asyncio
async def test_get_statistics_without_scores(service, session):
    """Статистика считает собеседования, даже если баллов ещё нет."""
    interviews = [MagicMock(score=None), MagicMock(score=None)]
    with patch.object(service, "get_history", AsyncMock(return_value=interviews)):
        assert await service.get_statistics(session, 1) == {
            "completed_count": 2,
            "average_score": 0,
            "best_score": 0,
        }


@pytest.mark.asyncio
async def test_get_statistics_with_scores(service, session):
    """Статистика считает среднее и лучший балл только по оценённым интервью."""
    interviews = [
        MagicMock(score=80),
        MagicMock(score=60),
        MagicMock(score=None),
    ]
    with patch.object(service, "get_history", AsyncMock(return_value=interviews)):
        stats = await service.get_statistics(session, 1)

    assert stats == {
        "completed_count": 3,
        "average_score": 70,
        "best_score": 80,
    }


@pytest.mark.asyncio
async def test_get_history_delegates_to_repository(service, session, interview):
    """История собеседований берётся из репозитория."""
    with patch(
        "services.interview_service.interview_repository.get_history_by_user_id",
        AsyncMock(return_value=[interview]),
    ) as get_history:
        result = await service.get_history(session, user_id=1)

    assert result == [interview]
    get_history.assert_awaited_once_with(session=session, user_id=1)


@pytest.mark.asyncio
async def test_start_interview_invalid_request(
    service, session, user, invalid_validation
):
    """Старт собеседования отклоняется при невалидной вакансии."""
    with (
        patch(
            "services.interview_service.subscription_service.ensure_can_start_interview",
            AsyncMock(),
        ),
        patch(
            "services.interview_service.llm_service.validate_interview_request",
            AsyncMock(return_value=invalid_validation),
        ),
    ):
        with pytest.raises(InvalidInterviewRequestError, match="Не вакансия"):
            await service.start_interview(
                session=session,
                user=user,
                difficulty=Difficulty.JUNIOR,
                position="asdf",
                requirements="qwerty",
                max_questions=10,
            )

    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_start_interview_success(
    service, session, user, question, question_pool, interview, valid_validation
):
    """Успешный старт создаёт интервью, пул вопросов и возвращает первый вопрос."""
    with (
        patch(
            "services.interview_service.subscription_service.ensure_can_start_interview",
            AsyncMock(),
        ),
        patch(
            "services.interview_service.llm_service.validate_interview_request",
            AsyncMock(return_value=valid_validation),
        ),
        patch(
            "services.interview_service.interview_repository.get_active_by_user_id",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.interview_service.interview_repository.create",
            AsyncMock(return_value=interview),
        ),
        patch(
            "services.interview_service.llm_service.generate_question_pool",
            AsyncMock(return_value=question_pool),
        ),
        patch(
            "services.interview_service.interview_question_repository.bulk_create",
            AsyncMock(return_value=[question]),
        ),
    ):
        result = await service.start_interview(
            session=session,
            user=user,
            difficulty=Difficulty.MIDDLE,
            position="Python Backend",
            requirements="FastAPI",
            max_questions=10,
        )

    assert result is question
    assert interview.question_count == 1
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_start_interview_interrupts_active(
    service, session, user, question, question_pool, interview, valid_validation
):
    """При новом старте активное собеседование помечается как прерванное."""
    active = MagicMock()
    active.status = InterviewStatus.IN_PROGRESS
    active.completed_at = None

    with (
        patch(
            "services.interview_service.subscription_service.ensure_can_start_interview",
            AsyncMock(),
        ),
        patch(
            "services.interview_service.llm_service.validate_interview_request",
            AsyncMock(return_value=valid_validation),
        ),
        patch(
            "services.interview_service.interview_repository.get_active_by_user_id",
            AsyncMock(return_value=active),
        ),
        patch(
            "services.interview_service.interview_repository.update",
            AsyncMock(),
        ) as update,
        patch(
            "services.interview_service.interview_repository.create",
            AsyncMock(return_value=interview),
        ),
        patch(
            "services.interview_service.llm_service.generate_question_pool",
            AsyncMock(return_value=question_pool),
        ),
        patch(
            "services.interview_service.interview_question_repository.bulk_create",
            AsyncMock(return_value=[question]),
        ),
    ):
        await service.start_interview(
            session=session,
            user=user,
            difficulty=Difficulty.MIDDLE,
            position="Python Backend",
            requirements="FastAPI",
            max_questions=10,
        )

    assert active.status == InterviewStatus.INTERRUPTED
    assert active.completed_at is not None
    update.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_interview_empty_pool_raises(
    service, session, user, interview, valid_validation
):
    """Старт падает с ошибкой LLM, если пул вопросов пустой."""
    with (
        patch(
            "services.interview_service.subscription_service.ensure_can_start_interview",
            AsyncMock(),
        ),
        patch(
            "services.interview_service.llm_service.validate_interview_request",
            AsyncMock(return_value=valid_validation),
        ),
        patch(
            "services.interview_service.interview_repository.get_active_by_user_id",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.interview_service.interview_repository.create",
            AsyncMock(return_value=interview),
        ),
        patch.object(
            service, "_create_questions_pool", AsyncMock(return_value=[])
        ),
    ):
        with pytest.raises(LLMServiceError):
            await service.start_interview(
                session=session,
                user=user,
                difficulty=Difficulty.MIDDLE,
                position="Python",
                requirements="Django",
                max_questions=10,
            )

    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_start_interview_limit_exceeded(service, session, user):
    """Старт блокируется, если исчерпан лимит FREE-подписки."""
    from exceptions import InterviewLimitExceededError

    with patch(
        "services.interview_service.subscription_service.ensure_can_start_interview",
        AsyncMock(side_effect=InterviewLimitExceededError("лимит")),
    ):
        with pytest.raises(InterviewLimitExceededError, match="лимит"):
            await service.start_interview(
                session=session,
                user=user,
                difficulty=Difficulty.MIDDLE,
                position="Python Backend",
                requirements="FastAPI",
                max_questions=10,
            )

    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_submit_answer_question_not_found(service, session):
    """Отправка ответа без текущего вопроса вызывает QuestionNotFoundError."""
    with patch(
        "services.interview_service.interview_question_repository.get_current_question",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(QuestionNotFoundError):
            await service.submit_answer(session, telegram_id=1, answer_text="ok")

    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_submit_answer_interrupted_interview(
    service, session, question, interview
):
    """Нельзя ответить на вопрос прерванного собеседования."""
    interview.status = InterviewStatus.INTERRUPTED
    with (
        patch(
            "services.interview_service.interview_question_repository.get_current_question",
            AsyncMock(return_value=question),
        ),
        patch(
            "services.interview_service.interview_repository.get_by_id",
            AsyncMock(return_value=interview),
        ),
    ):
        with pytest.raises(InterviewNotFoundOrInterraptedError):
            await service.submit_answer(session, 12345, "ответ")


@pytest.mark.asyncio
async def test_submit_answer_completed_interview(
    service, session, question, interview
):
    """Нельзя ответить на вопрос завершённого собеседования."""
    interview.status = InterviewStatus.COMPLETED
    with (
        patch(
            "services.interview_service.interview_question_repository.get_current_question",
            AsyncMock(return_value=question),
        ),
        patch(
            "services.interview_service.interview_repository.get_by_id",
            AsyncMock(return_value=interview),
        ),
    ):
        with pytest.raises(InterviewIsCompletedError):
            await service.submit_answer(session, 12345, "ответ")


@pytest.mark.asyncio
async def test_submit_answer_already_answered(
    service, session, question, interview
):
    """Повторный ответ на тот же вопрос запрещён."""
    with (
        patch(
            "services.interview_service.interview_question_repository.get_current_question",
            AsyncMock(return_value=question),
        ),
        patch(
            "services.interview_service.interview_repository.get_by_id",
            AsyncMock(return_value=interview),
        ),
        patch(
            "services.interview_service.user_answer_repository.get_by_question_id",
            AsyncMock(return_value=MagicMock()),
        ),
    ):
        with pytest.raises(AlreadyAnsweredError):
            await service.submit_answer(session, 12345, "ответ")


@pytest.mark.asyncio
async def test_submit_answer_returns_next_question(
    service,
    session,
    question,
    interview,
    answer_evaluation,
    user_answer,
):
    """После ответа возвращается следующий неотвеченный вопрос."""
    next_question = MagicMock()
    next_question.question_text = "Следующий вопрос"

    with (
        patch(
            "services.interview_service.interview_question_repository.get_current_question",
            AsyncMock(side_effect=[question, next_question]),
        ),
        patch(
            "services.interview_service.interview_repository.get_by_id",
            AsyncMock(return_value=interview),
        ),
        patch(
            "services.interview_service.user_answer_repository.get_by_question_id",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.interview_service.llm_service.evaluate_answer",
            AsyncMock(return_value=answer_evaluation),
        ),
        patch(
            "services.interview_service.user_answer_repository.create",
            AsyncMock(return_value=user_answer),
        ),
    ):
        result = await service.submit_answer(session, 12345, "мой ответ")

    assert result.next_question is next_question
    assert result.user_answer is user_answer
    assert result.evaluation is None
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_submit_answer_finishes_interview(
    service,
    session,
    question,
    interview,
    answer_evaluation,
    user_answer,
    interview_evaluation,
):
    """Ответ на последний вопрос завершает собеседование с итоговой оценкой."""
    with (
        patch(
            "services.interview_service.interview_question_repository.get_current_question",
            AsyncMock(side_effect=[question, None]),
        ),
        patch(
            "services.interview_service.interview_repository.get_by_id",
            AsyncMock(return_value=interview),
        ),
        patch(
            "services.interview_service.user_answer_repository.get_by_question_id",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.interview_service.llm_service.evaluate_answer",
            AsyncMock(return_value=answer_evaluation),
        ),
        patch(
            "services.interview_service.user_answer_repository.create",
            AsyncMock(return_value=user_answer),
        ),
        patch.object(
            service,
            "finish_interview",
            AsyncMock(return_value=interview_evaluation),
        ),
    ):
        result = await service.submit_answer(session, 12345, "финальный ответ")

    assert result.next_question is None
    assert result.evaluation is interview_evaluation
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_finish_interview_no_answers(service, session, interview):
    """Нельзя завершить собеседование без ответов кандидата."""
    with patch(
        "services.interview_service.user_answer_repository.get_all_by_interview_id",
        AsyncMock(return_value=[]),
    ):
        with pytest.raises(NoAnswerError):
            await service.finish_interview(session, interview)


@pytest.mark.asyncio
async def test_finish_interview_success(
    service, session, interview, user_answer, interview_evaluation
):
    """Успешное завершение сохраняет итоговую оценку и статус COMPLETED."""
    with (
        patch(
            "services.interview_service.user_answer_repository.get_all_by_interview_id",
            AsyncMock(return_value=[user_answer]),
        ),
        patch(
            "services.interview_service.llm_service.evaluate_interview",
            AsyncMock(return_value=interview_evaluation),
        ),
    ):
        result = await service.finish_interview(session, interview)

    assert result is interview_evaluation
    assert interview.status == InterviewStatus.COMPLETED
    assert interview.score == interview_evaluation.score
    assert interview.summary == interview_evaluation.summary
    assert interview.completed_at is not None
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_interrupted_interview_not_found(service, session):
    """Прерывание без активного собеседования вызывает ошибку."""
    with patch(
        "services.interview_service.interview_repository.get_active_by_user_id",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(InterviewNotFoundOrInterraptedError):
            await service.interrupted_interview(session, user_id=1)


@pytest.mark.asyncio
async def test_interrupted_interview_success(service, session, interview):
    """Активное собеседование успешно помечается как прерванное."""
    with patch(
        "services.interview_service.interview_repository.get_active_by_user_id",
        AsyncMock(return_value=interview),
    ):
        await service.interrupted_interview(session, user_id=1)

    assert interview.status == InterviewStatus.INTERRUPTED
    assert interview.completed_at is not None
    session.commit.assert_awaited()
