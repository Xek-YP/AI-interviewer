import asyncio

from openai import (
    AsyncOpenAI,
    APIStatusError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError
)

from constants.interview import (
    QUESTION_PROMPT, DEEPSEEK_BASE_URL,
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


class LLMService:
    """Сервис работы с LLM."""
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key.get_secret_value(),
            base_url=DEEPSEEK_BASE_URL,
            max_retries=0,
        )
        
    async def generate_question(
        self,
        difficulty: Difficulty,
        category: str
    ) -> str:
        """Генерирует вопрос для технического собеседовнаия."""

        prompt = QUESTION_PROMPT.format(
            difficulty=difficulty.value,
            category=category
        )

        attempts = 1

        while attempts <= MAX_LLM_ATTEMPTS:
            try:
                response = await self.client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=[
                        {
                            'role': 'system',
                            'content': 'Ты технический интервьювер с 10 летним стажем. Отвечай только текстом.'
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.7,
                    max_tokens=150,
                    extra_body={
                        'thinking': {
                            'type': 'disabled'
                        }
                    }
                )

                question = response.choices[0].message.content
                if not question:
                    if attempts == MAX_LLM_ATTEMPTS:
                        raise LLMTemporaryError('Ответ LLM пуст.')
                    attempts += 1
                    await asyncio.sleep(LLM_RETRY_DELAY)
                    continue
                return question
            except AuthenticationError as e:
                raise LLMAuthenticationError(
                    'Проблема аутентификации API DeepSeek'
                ) from e
            except RateLimitError as e:
                if attempts == MAX_LLM_ATTEMPTS:
                    raise LLMTemporaryError('Превышен rate limit LLM.') from e
                attempts +=1
                await asyncio.sleep(LLM_RETRY_DELAY)
            except APIStatusError as e:
                if e.status_code == 402:
                    raise LLMInsufficientBalanceError(
                        'Недостаточно средств на балансе LLM.'
                    ) from e
                elif e.status_code >= 500:
                    if attempts == MAX_LLM_ATTEMPTS:
                        raise LLMTemporaryError('Ошибка сервера LLM.') from e
                    attempts += 1
                    await asyncio.sleep(LLM_RETRY_DELAY)
                else:
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
                        'Не удалось установить соединения с LLM.'
                    ) from e
                attempts += 1
                await asyncio.sleep(LLM_RETRY_DELAY)


llm_service = LLMService()