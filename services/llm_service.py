import asyncio

from openai import AsyncOpenAI

from constants.interview import (
    QUESTION_PROMPT, DEEPSEEK_BASE_URL,
    MAX_LLM_ATTEMPTS, LLM_RETRY_DELAY
)
from config.settings import Settings
from database.enums import Difficulty

class LLMService:
    """Сервис работы с LLM."""
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

        client = AsyncOpenAI(
            api_key=Settings.deepseek_api_key,
            base_url=DEEPSEEK_BASE_URL,
        )
        attempts = 1

        while attempts <= MAX_LLM_ATTEMPTS:
            try:
                response = await client.chat.completions.create(
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
                    raise
                attempts += 1
                await asyncio.sleep(LLM_RETRY_DELAY)
            except Exception as e:
                attempts += 1
                await asyncio.sleep(LLM_RETRY_DELAY)
        return question
