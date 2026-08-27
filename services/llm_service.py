import asyncio
import json

from openai import (
    AsyncOpenAI,
    APIStatusError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError
)
from pydantic import ValidationError

from constants.interview import (
    ANSWER_PROMPT, INTERVIEW_EVALUATION_PROMPT, INTERVIEW_VALIDATION_PROMPT,
    QUESTION_POOL_PROMPT, DEEPSEEK_BASE_URL,
    MAX_LLM_ATTEMPTS, LLM_RETRY_DELAY
)
from config.settings import settings
from database.enums import Difficulty
from exceptions.llm_exception import (
    LLMServiceError,
    LLMAuthenticationError,
    LLMInsufficientBalanceError,
    LLMTemporaryError
)
from schemas.answer import AnswerEvaluation
from schemas.interview import InterviewEvaluation, InterviewRequestValidation
from schemas.interview_question import InterviewQuestionPool


class LLMService:
    """Сервис работы с LLM."""
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key.get_secret_value(),
            base_url=DEEPSEEK_BASE_URL,
            max_retries=0,
        )

    async def _request_llm(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: dict[str, str] | None = None
        ) -> str:
        """Отправляет запрос в LLM с повторными попытками."""

        attempts = 1

        while attempts <= MAX_LLM_ATTEMPTS:
            try:
                response = await self.client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    extra_body={
                        'thinking': {
                            'type': 'disabled'
                        }
                    }
                )

                content = response.choices[0].message.content

                if not content:
                    if attempts == MAX_LLM_ATTEMPTS:
                        raise LLMTemporaryError(
                            "Ответ LLM пуст."
                        )

                    attempts += 1
                    await asyncio.sleep(LLM_RETRY_DELAY)
                    continue

                return content

            except AuthenticationError as e:
                raise LLMAuthenticationError(
                    'Проблема аутентификации API DeepSeek.'
                ) from e

            except RateLimitError as e:
                if attempts == MAX_LLM_ATTEMPTS:
                    raise LLMTemporaryError(
                        'Превышен rate limit LLM.'
                    ) from e

                attempts += 1
                await asyncio.sleep(LLM_RETRY_DELAY)

            except APIStatusError as e:
                if e.status_code == 402:
                    raise LLMInsufficientBalanceError(
                        'Недостаточно средств на балансе LLM.'
                    ) from e

                if e.status_code >= 500:
                    if attempts == MAX_LLM_ATTEMPTS:
                        raise LLMTemporaryError(
                            'Ошибка сервера LLM.'
                        ) from e

                    attempts += 1
                    await asyncio.sleep(LLM_RETRY_DELAY)
                    continue

                raise LLMServiceError(
                    f'Ошибка LLM: HTTP {e.status_code}.'
                ) from e

            except APITimeoutError as e:
                if attempts == MAX_LLM_ATTEMPTS:
                    raise LLMTemporaryError(
                        'Превышено время ожидания ответа от LLM.'
                    ) from e

                attempts += 1
                await asyncio.sleep(LLM_RETRY_DELAY)

            except APIConnectionError as e:
                if attempts == MAX_LLM_ATTEMPTS:
                    raise LLMTemporaryError(
                        'Не удалось установить соединение с LLM.'
                    ) from e

                attempts += 1
                await asyncio.sleep(LLM_RETRY_DELAY)

        raise LLMTemporaryError(
            'Не удалось получить ответ от LLM после всех попыток.'
        )

    async def generate_question_pool(
        self,
        difficulty: Difficulty,
        position: str,
        requirements: str,
        max_questions: int,
    ) -> InterviewQuestionPool:
        """Генерирует пул вопрос для технического собеседования."""

        prompt = QUESTION_POOL_PROMPT.format(
            difficulty=difficulty.value,
            position=position,
            requirements=requirements,
            max_questions=max_questions
        )

        messages = [
            {
                'role': 'system',
                'content': (
                    "Ты составляешь пул вопросов для технического собеседования. "
                    "Формулируй вопросы как опытный технический интервьюер. "
                    "Не давай ответы на вопросы."
                ),
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ]
        response = await self._request_llm(
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            response_format={'type': 'json_object'},
        )
        try:
            data = json.loads(response)
            pool = InterviewQuestionPool.model_validate(data)
        except json.JSONDecodeError as e:
            raise LLMServiceError(
                'LLM вернула JSON, не соответствующего схеме пула вопросов'
            ) from e
        except ValidationError as e:
            raise LLMServiceError(
                'LLM вернула JSON, не соответствующего схеме пула вопросов'
            ) from e
        if 5 > len(pool.questions) > max_questions:
            raise LLMServiceError(
                'LLM сгенерировала больше вопросов, чем разрешено.'
            )

        return pool

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        position: str,
        requirements: str,
        difficulty: str,
        category: str,
    ) -> AnswerEvaluation:
        """Оценивает ответ пользователя на поставленный ему вопрос."""

        prompt = ANSWER_PROMPT.format(
            question=question,
            answer=answer,
            position=position,
            requirements=requirements,
            difficulty=difficulty.value,
            category=category
        )

        messages = [
            {
                'role': 'system',
                'content': ('Ты технический интервьювер с 10-летним стажем. '
                    'Отвечай строго в формате JSON.'
                ),
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ]

        response = await self._request_llm(
            messages=messages,
            temperature=0.2,
            max_tokens=500,
            response_format={'type': 'json_object'},
        )

        try:
            data = json.loads(response)
            return AnswerEvaluation.model_validate(data)
        except json.JSONDecodeError as e:
            raise LLMServiceError(
                'LLM вернула некорректный формат оценки ответа'
            ) from e
        except ValidationError as e:
            raise LLMServiceError(
                'LLM вернула JSON не соответствующий схеме оценки.'
            ) from e

    async def evaluate_interview(
        self,
        position: str,
        requirements: str,
        difficulty: Difficulty,
        answers: str
    ) -> InterviewEvaluation:
        """Оценивает кандидата после завершения собеседовнаия."""

        prompt = INTERVIEW_EVALUATION_PROMPT.format(
            position=position,
            requirements=requirements,
            difficulty=difficulty.value,
            answers=answers
        )

        messages = [
            {
                'role': 'system',
                'content': ('Ты оцениваешь кандидатов на технических собеседованиях')
            },
            {
                'role': 'user',
                'content': prompt
            },
        ]

        response = await self._request_llm(
            messages=messages,
            temperature=0.2,
            max_tokens=1000,
            response_format={
                'type': 'json_object'
            },
        )

        try:
            data = json.loads(response)
            return InterviewEvaluation.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise LLMServiceError(
                'LLM вернула конечную оценку не праильной формы.'
            ) from e


    async def validate_interview_request(
        self,
        position: str,
        requirements: str,
    ) -> InterviewRequestValidation:
        """Проверяет корректность данных вакансии."""

        prompt = INTERVIEW_VALIDATION_PROMPT.format(
            position=position,
            requirements=requirements,
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Ты проверяешь данные для технического интервью. "
                    "Отвечай только JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response = await self._request_llm(
            messages=messages,
            temperature=0,
            max_tokens=200,
            response_format={
                "type": "json_object"
            },
        )

        try:
            data = json.loads(response)

            return InterviewRequestValidation.model_validate(
                data
            )

        except (json.JSONDecodeError, ValidationError) as e:
            raise LLMServiceError(
                "LLM вернула некорректный ответ при проверке вакансии."
            ) from e

llm_service = LLMService()
