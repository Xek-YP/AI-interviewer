import asyncio

from openai import AsyncOpenAI

from database.enums import Difficulty
from constants.interview import QUESTION_PROMPT

from os import getenv

from dotenv import load_dotenv

load_dotenv()

async def test_generate_question():
    """Тестирует генерацию вопросов через DeepSeek."""

    client = AsyncOpenAI(
        api_key=getenv('DEEPSEEK_API_KEY'),
        base_url="https://api.deepseek.com",
    )

    test_cases = [
        (Difficulty.JUNIOR, "Основы Python"),
        (Difficulty.MIDDLE, "ООП"),
        (Difficulty.SENIOR, "Асинхронность"),
    ]

    for difficulty, category in test_cases:
        print(f"\n{'=' * 50}")
        print(f"Тест: {difficulty.value} | {category}")
        print(f"{'=' * 50}")

        prompt = QUESTION_PROMPT.format(
            difficulty=difficulty.value,
            category=category,
        )

        try:
            response = await client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
                max_tokens=150,
            )

            question = response.choices[0].message.content

            print(f"Вопрос:\n{question}")

        except Exception as e:
            print(f"Ошибка: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_generate_question())