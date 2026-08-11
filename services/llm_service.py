from freeflow_llm import FreeFlowClient

from constants.interview import QUESTION_PROMPT
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

        async with FreeFlowClient() as client:
            response = await client.async_chat(
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ],
                model="gemini-3.6-flash",
                temperature=0.7,
                max_tokens=150,
            )
        return response.content
