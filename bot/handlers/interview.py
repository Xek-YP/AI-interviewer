from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.buttons_text import START_INTERVIEW, DIFFICULTY_BUTTONS
from bot.keyboards.difficulty_keyboard import create_difficulty_keyboard
from .start import MAIN_KEYBOARD
from database.session import AsyncSessionLocal
from services.interview_service import interview_service
from services.user_service import user_service

router = Router()

DIFFICULTY_KEYBOARD = create_difficulty_keyboard()

@router.message(F.text == START_INTERVIEW)
async def start_interview_handler(message: Message):
    await message.answer(
        'Выберите сложность собеседовнаия.',
        reply_markup=DIFFICULTY_KEYBOARD
    )

@router.message(F.text.in_(DIFFICULTY_BUTTONS))
async def difficulty_handler(message: Message):
    difficulty = DIFFICULTY_BUTTONS[message.text]

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
            difficulty=difficulty,
            max_questions=5,
        )

    await message.answer(
        question.question_text,
        reply_markup=MAIN_KEYBOARD,
    )

@router.message(F.text)
async def submit_answer(message: Message):
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        result = await interview_service.submit_answer(
            session=session,
            telegram_id=message.from_user.id,
            answer_text=message.text,
        )

        if result.next_question:
            response_text = (
                    f"📊 Ваша оценка: {result.user_answer.score}/100\n\n"
                    f"💪 Сильные стороны:\n{result.user_answer.strengths}\n\n"
                    f"📉 Слабые стороны:\n{result.user_answer.weaknesses}\n\n"
                    f"🎯 Уверенность: {result.user_answer.confidence * 100:.0f}%\n\n"
                    f"Следующий вопрос:\n{result.next_question.question_text}"
                )
        else:
            response_text = (
                f"📊 Ваша оценка: {result.user_answer.score}/100\n\n"
                f"💪 Сильные стороны:\n{result.user_answer.strengths}\n\n"
                f"📉 Слабые стороны:\n{result.user_answer.weaknesses}\n\n"
                f"🎯 Уверенность: {result.user_answer.confidence * 100:.0f}%\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⭐ Собеседование завершено.\n"
                f"🏆 Итоговая оценка: {result.interview_score} ⭐"
            )

        await message.answer(
            response_text
        )
