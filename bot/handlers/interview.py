from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.messages import END_INTERVIEW_MESSAGE
from bot.handlers.start import MAIN_KEYBOARD
from bot.keyboards.buttons_text import (
    END_INTERVIEW,
    MAIN_MENU_BUTTONS,
)
from bot.keyboards.interview_keyboard import create_interview_keyboard
from bot.states.interview import InterviewStates

from database.session import AsyncSessionLocal
from services.interview_service import interview_service
from services.user_service import user_service


router = Router()

INTERVIEW_KEYBOARD = create_interview_keyboard()


@router.message(
    InterviewStates.answering,
    F.text.not_in(MAIN_MENU_BUTTONS | {END_INTERVIEW}),
)
async def submit_answer_handler(
    message: Message,
    state: FSMContext,
):
    """Обработка ответа пользователя."""

    if message.from_user is None:
        return

    if not message.text:
        return

    async with AsyncSessionLocal() as session:
        result = await interview_service.submit_answer(
            session=session,
            telegram_id=message.from_user.id,
            answer_text=message.text,
        )

    if result.next_question:
        response_text = (
            f'📊 Оценка ответа: '
            f'{result.user_answer.score}/100\n\n'
            f'💪 Сильные стороны:\n'
            f'{result.user_answer.strengths}\n\n'
            f'📉 Слабые стороны:\n'
            f'{result.user_answer.weaknesses}\n\n'
            '━━━━━━━━━━━━━━━━━━\n\n'
            'Следующий вопрос:\n'
            f'{result.next_question.question_text}'
        )

        await message.answer(
            response_text,
            reply_markup=INTERVIEW_KEYBOARD,
        )

        return

    evaluation = result.evaluation

    await state.clear()

    response_text = (
        '🏁 Собеседование завершено!\n\n'
        f'⭐ Итоговая оценка: '
        f'{evaluation.score}/100\n\n'
        f'📝 Общий вывод:\n'
        f'{evaluation.summary}\n\n'
        f'💪 Сильные стороны:\n'
        f'{interview_service._format_evaluation_items(evaluation.strengths)}\n\n'
        f'📉 Слабые стороны:\n'
        f'{interview_service._format_evaluation_items(evaluation.weaknesses)}\n\n'
        f'🎯 Рекомендация:\n'
        f'{evaluation.recommendation}'
    )

    await message.answer(
        response_text,
        reply_markup=MAIN_KEYBOARD,
    )


@router.message(
    InterviewStates.answering,
    F.text == END_INTERVIEW,
)
async def end_interview_handler(
    message: Message,
    state: FSMContext,
):
    """Досрочное завершение собеседования."""

    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.get_user(
            session=session,
            telegram_id=message.from_user.id,
        )

        await interview_service.interrupted_interview(
            session=session,
            user_id=user.id,
        )

    await state.clear()

    await message.answer(
        END_INTERVIEW_MESSAGE,
        reply_markup=MAIN_KEYBOARD,
    )