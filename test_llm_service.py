# test_llm_service.py
import asyncio
from pathlib import Path
import sys

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent))

from services.llm_service import LLMService
from database.enums import Difficulty


async def test_generate_question():
    """Тестирует генерацию вопроса."""
    service = LLMService()
    
    # Тестируем разные сложности
    test_cases = [
        (Difficulty.JUNIOR, "Основы Python"),
        (Difficulty.MIDDLE, "ООП"),
        (Difficulty.SENIOR, "Асинхронность"),
    ]
    
    for difficulty, category in test_cases:
        print(f"\n{'='*50}")
        print(f"🎯 Тест: {difficulty.value} | {category}")
        print(f"{'='*50}")
        
        try:
            question = await service.generate_question(
                difficulty=difficulty,
                category=category
            )
            print(f"✅ Вопрос:\n{question}\n")
        except Exception as e:
            print(f"❌ Ошибка: {e}\n")


if __name__ == "__main__":
    asyncio.run(test_generate_question())