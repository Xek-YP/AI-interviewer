import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

from database.enums import Difficulty
from exceptions.llm_exception import (
    LLMAuthenticationError,
    LLMInsufficientBalanceError,
    LLMServiceError,
    LLMTemporaryError,
)
from schemas.answer import AnswerEvaluation
from schemas.interview import InterviewEvaluation, InterviewRequestValidation
from schemas.interview_question import InterviewQuestionPool
from services.llm_service import LLMService


@pytest.fixture
def llm():
    with patch("services.llm_service.AsyncOpenAI"):
        service = LLMService()
        service.client = MagicMock()
        service.client.chat.completions.create = AsyncMock()
        return service


def _completion(content: str | None):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def _http_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        request=httpx.Request("POST", "https://api.deepseek.com/v1/chat"),
    )


@pytest.mark.asyncio
async def test_request_llm_success(llm):
    """Успешный ответ LLM возвращается как текст."""
    llm.client.chat.completions.create.return_value = _completion('{"ok": true}')

    result = await llm._request_llm(
        messages=[{"role": "user", "content": "hi"}],
        temperature=0,
        max_tokens=10,
    )

    assert result == '{"ok": true}'


@pytest.mark.asyncio
async def test_request_llm_retries_empty_then_succeeds(llm):
    """Пустой ответ LLM приводит к повтору запроса и успеху."""
    llm.client.chat.completions.create.side_effect = [
        _completion(None),
        _completion('{"ok": true}'),
    ]

    with patch("services.llm_service.asyncio.sleep", AsyncMock()):
        result = await llm._request_llm(
            messages=[{"role": "user", "content": "hi"}],
            temperature=0,
            max_tokens=10,
        )

    assert result == '{"ok": true}'
    assert llm.client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_request_llm_empty_after_retries(llm):
    """После исчерпания попыток пустой ответ даёт LLMTemporaryError."""
    llm.client.chat.completions.create.return_value = _completion(None)

    with patch("services.llm_service.asyncio.sleep", AsyncMock()):
        with pytest.raises(LLMTemporaryError, match="пуст"):
            await llm._request_llm(
                messages=[{"role": "user", "content": "hi"}],
                temperature=0,
                max_tokens=10,
            )


@pytest.mark.asyncio
async def test_request_llm_authentication_error(llm):
    """Ошибка аутентификации API мапится в LLMAuthenticationError."""
    llm.client.chat.completions.create.side_effect = AuthenticationError(
        message="bad key",
        response=_http_response(401),
        body=None,
    )

    with pytest.raises(LLMAuthenticationError):
        await llm._request_llm(
            messages=[{"role": "user", "content": "hi"}],
            temperature=0,
            max_tokens=10,
        )


@pytest.mark.asyncio
async def test_request_llm_insufficient_balance(llm):
    """HTTP 402 мапится в LLMInsufficientBalanceError."""
    llm.client.chat.completions.create.side_effect = APIStatusError(
        message="payment required",
        response=_http_response(402),
        body=None,
    )

    with pytest.raises(LLMInsufficientBalanceError):
        await llm._request_llm(
            messages=[{"role": "user", "content": "hi"}],
            temperature=0,
            max_tokens=10,
        )


@pytest.mark.asyncio
async def test_request_llm_server_error_retries(llm):
    """Серверные ошибки LLM ретраятся и затем дают временную ошибку."""
    llm.client.chat.completions.create.side_effect = APIStatusError(
        message="server error",
        response=_http_response(500),
        body=None,
    )

    with patch("services.llm_service.asyncio.sleep", AsyncMock()):
        with pytest.raises(LLMTemporaryError, match="сервера"):
            await llm._request_llm(
                messages=[{"role": "user", "content": "hi"}],
                temperature=0,
                max_tokens=10,
            )

    assert llm.client.chat.completions.create.await_count == 3


@pytest.mark.asyncio
async def test_request_llm_client_http_error(llm):
    """Клиентские HTTP-ошибки LLM не ретраятся."""
    llm.client.chat.completions.create.side_effect = APIStatusError(
        message="bad request",
        response=_http_response(400),
        body=None,
    )

    with pytest.raises(LLMServiceError, match="HTTP 400"):
        await llm._request_llm(
            messages=[{"role": "user", "content": "hi"}],
            temperature=0,
            max_tokens=10,
        )


@pytest.mark.asyncio
async def test_request_llm_rate_limit_exhausted(llm):
    """Исчерпание rate limit после ретраев даёт LLMTemporaryError."""
    llm.client.chat.completions.create.side_effect = RateLimitError(
        message="rate limit",
        response=_http_response(429),
        body=None,
    )

    with patch("services.llm_service.asyncio.sleep", AsyncMock()):
        with pytest.raises(LLMTemporaryError, match="rate limit"):
            await llm._request_llm(
                messages=[{"role": "user", "content": "hi"}],
                temperature=0,
                max_tokens=10,
            )


@pytest.mark.asyncio
async def test_request_llm_timeout_exhausted(llm):
    """Таймаут после всех попыток даёт LLMTemporaryError."""
    llm.client.chat.completions.create.side_effect = APITimeoutError(
        request=httpx.Request("POST", "https://api.deepseek.com/v1/chat")
    )

    with patch("services.llm_service.asyncio.sleep", AsyncMock()):
        with pytest.raises(LLMTemporaryError, match="ожидания"):
            await llm._request_llm(
                messages=[{"role": "user", "content": "hi"}],
                temperature=0,
                max_tokens=10,
            )


@pytest.mark.asyncio
async def test_request_llm_connection_exhausted(llm):
    """Ошибка соединения после ретраев даёт LLMTemporaryError."""
    llm.client.chat.completions.create.side_effect = APIConnectionError(
        request=httpx.Request("POST", "https://api.deepseek.com/v1/chat"),
        message="connection failed",
    )

    with patch("services.llm_service.asyncio.sleep", AsyncMock()):
        with pytest.raises(LLMTemporaryError, match="соединение"):
            await llm._request_llm(
                messages=[{"role": "user", "content": "hi"}],
                temperature=0,
                max_tokens=10,
            )


@pytest.mark.asyncio
async def test_generate_question_pool_success(llm, question_pool):
    """Корректный JSON пула вопросов парсится в InterviewQuestionPool."""
    payload = question_pool.model_dump(mode="json")
    with patch.object(
        llm, "_request_llm", AsyncMock(return_value=json.dumps(payload))
    ):
        result = await llm.generate_question_pool(
            difficulty=Difficulty.MIDDLE,
            position="Python Backend",
            requirements="FastAPI",
            max_questions=10,
        )

    assert isinstance(result, InterviewQuestionPool)
    assert len(result.questions) == 5


@pytest.mark.asyncio
async def test_generate_question_pool_invalid_json(llm):
    """Невалидный JSON пула вопросов приводит к LLMServiceError."""
    with patch.object(llm, "_request_llm", AsyncMock(return_value="not-json")):
        with pytest.raises(LLMServiceError, match="пула вопросов"):
            await llm.generate_question_pool(
                difficulty=Difficulty.MIDDLE,
                position="Python Backend",
                requirements="FastAPI",
                max_questions=10,
            )


@pytest.mark.asyncio
async def test_generate_question_pool_invalid_schema(llm):
    """JSON пула, не подходящий под схему, приводит к LLMServiceError."""
    with patch.object(
        llm, "_request_llm", AsyncMock(return_value='{"questions": "bad"}')
    ):
        with pytest.raises(LLMServiceError, match="пула вопросов"):
            await llm.generate_question_pool(
                difficulty=Difficulty.MIDDLE,
                position="Python Backend",
                requirements="FastAPI",
                max_questions=10,
            )


@pytest.mark.asyncio
async def test_evaluate_answer_success(llm):
    """Корректная оценка ответа парсится в AnswerEvaluation."""
    payload = {
        "score": 80,
        "strengths": ["Структура"],
        "weaknesses": ["Примеры"],
        "confidence": 0.9,
    }
    with patch.object(
        llm, "_request_llm", AsyncMock(return_value=json.dumps(payload))
    ):
        result = await llm.evaluate_answer(
            question="Что такое GIL?",
            answer="Блокировка интерпретатора",
            position="Python Backend",
            requirements="Python",
            difficulty=Difficulty.MIDDLE,
            category="Python",
        )

    assert isinstance(result, AnswerEvaluation)
    assert result.score == 80


@pytest.mark.asyncio
async def test_evaluate_answer_invalid_json(llm):
    """Невалидный JSON оценки ответа приводит к LLMServiceError."""
    with patch.object(llm, "_request_llm", AsyncMock(return_value="oops")):
        with pytest.raises(LLMServiceError, match="оценки ответа"):
            await llm.evaluate_answer(
                question="Q",
                answer="A",
                position="Dev",
                requirements="Python",
                difficulty=Difficulty.MIDDLE,
                category="Python",
            )


@pytest.mark.asyncio
async def test_evaluate_interview_success(llm):
    """Корректная итоговая оценка парсится в InterviewEvaluation."""
    payload = {
        "score": 75,
        "summary": "Хороший кандидат",
        "strengths": ["База"],
        "weaknesses": ["Опыт"],
        "recommendation": "hire",
        "confidence": 0.8,
    }
    with patch.object(
        llm, "_request_llm", AsyncMock(return_value=json.dumps(payload))
    ):
        result = await llm.evaluate_interview(
            position="Python Backend",
            requirements="FastAPI",
            difficulty=Difficulty.MIDDLE,
            answers="answers text",
        )

    assert isinstance(result, InterviewEvaluation)
    assert result.score == 75


@pytest.mark.asyncio
async def test_evaluate_interview_invalid_payload(llm):
    """Неполная итоговая оценка LLM приводит к LLMServiceError."""
    with patch.object(llm, "_request_llm", AsyncMock(return_value="{}")):
        with pytest.raises(LLMServiceError, match="конечную оценку"):
            await llm.evaluate_interview(
                position="Python Backend",
                requirements="FastAPI",
                difficulty=Difficulty.MIDDLE,
                answers="answers text",
            )


@pytest.mark.asyncio
async def test_validate_interview_request_success(llm):
    """Корректный ответ валидации вакансии парсится в схему."""
    payload = {"valid": True, "reason": "ok"}
    with patch.object(
        llm, "_request_llm", AsyncMock(return_value=json.dumps(payload))
    ):
        result = await llm.validate_interview_request(
            position="Python Backend",
            requirements="FastAPI, PostgreSQL",
        )

    assert isinstance(result, InterviewRequestValidation)
    assert result.valid is True


@pytest.mark.asyncio
async def test_validate_interview_request_invalid_payload(llm):
    """Некорректный ответ валидации вакансии приводит к LLMServiceError."""
    with patch.object(llm, "_request_llm", AsyncMock(return_value="[]")):
        with pytest.raises(LLMServiceError, match="проверке вакансии"):
            await llm.validate_interview_request(
                position="x",
                requirements="y",
            )
