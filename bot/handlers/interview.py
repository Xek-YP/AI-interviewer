from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.buttons_text import START_INTERVIEW
from database.enums import Difficulty
from database.session import AsyncSessionLocal
from services.interview_service import interview_service
from services.user_service import user_service

router = Router()


@router.message(F.text == START_INTERVIEW)
async def start_interview_handler(message: Message):
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.get_user(
            session=session,
            telegram_id=message.from_user.id,
        )
        question = await interview_service.start_interview(
            session=session,
            user_id=user.id,
            difficulty=Difficulty.JUNIOR,
            max_questions=5,
        )
        await message.answer(
            question.question_text,
        )


@router.message(F.text)
async def submit_answer(message: Message):
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        question, answer = await interview_service.submit_answer(
            session=session,
            telegram_id=message.from_user.id,
            answer_text=message.text,
        )
        response_text = (
                f"📊 Ваша оценка: {answer.score}/100\n\n"
                f"💪 Сильные стороны:\n{answer.strengths}\n\n"
                f"📉 Слабые стороны:\n{answer.weaknesses}\n\n"
                f"🎯 Уверенность: {answer.confidence * 100:.0f}%\n\n"
                f"Следующий вопрос:\n{question.question_text}"
            )
        await message.answer(
            response_text
        )