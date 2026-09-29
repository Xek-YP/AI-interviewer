from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.start import MAIN_KEYBOARD
from bot.handlers.messages import GENERATED_QUESTIONS
from bot.keyboards.buttons_text import (
    START_INTERVIEW,
    DIFFICULTY_BUTTONS,
)
from bot.keyboards.difficulty_keyboard import create_difficulty_keyboard
from bot.keyboards.interview_keyboard import create_interview_keyboard
from bot.states.interview import InterviewStates

from database.session import AsyncSessionLocal
from exceptions import InvalidInterviewRequestError
from services.interview_service import interview_service
from services.user_service import user_service


router = Router()

DIFFICULTY_KEYBOARD = create_difficulty_keyboard()
INTERVIEW_KEYBOARD = create_interview_keyboard()


@router.message(F.text == START_INTERVIEW)
async def start_interview_handler(
    message: Message,
    state: FSMContext,
):
    """Запуск создания интервью."""

    await state.set_state(
        InterviewStates.waiting_position
    )

    await message.answer(
        'Введите название должности, на которую хотите пройти собеседование.'
    )


@router.message(InterviewStates.waiting_position)
async def position_handler(
    message: Message,
    state: FSMContext,
):
    """Получение позиции."""

    if not message.text:
        return

    position = message.text.strip()

    if len(position) < 4:
        await message.answer(
            'Название должности слишком короткое. '
            'Введите реальную должность.'
        )
        return

    await state.update_data(
        position=position
    )

    await state.set_state(
        InterviewStates.waiting_requirements
    )

    await message.answer(
        'Теперь отправьте требования вакансии.\n\n'
        'Например:\n'
        'Python, Django, PostgreSQL, Redis, Docker.'
    )


@router.message(InterviewStates.waiting_requirements)
async def requirements_handler(
    message: Message,
    state: FSMContext,
):
    """Получение требований вакансии."""

    if not message.text:
        return

    requirements = message.text.strip()

    if len(requirements) < 15:
        await message.answer(
            'Введите больше информации о вакансии.'
        )
        return

    await state.update_data(
        requirements=requirements
    )

    await state.set_state(
        InterviewStates.waiting_difficulty
    )

    await message.answer(
        'Выберите сложность собеседования.',
        reply_markup=DIFFICULTY_KEYBOARD,
    )


@router.message(
    InterviewStates.waiting_difficulty,
    F.text.in_(DIFFICULTY_BUTTONS),
)
async def difficulty_handler(
    message: Message,
    state: FSMContext,
):
    """Создание интервью."""

    if message.from_user is None:
        return

    if not message.text:
        return

    difficulty = DIFFICULTY_BUTTONS[message.text]

    data = await state.get_data()

    position = data.get('position')
    requirements = data.get('requirements')

    if not position or not requirements:
        await state.clear()

        await message.answer(
            'Ошибка создания интервью. Начните заново.',
            reply_markup=MAIN_KEYBOARD,
        )
        return

    try:
        async with AsyncSessionLocal() as session:
            user = await user_service.get_user(
                session=session,
                telegram_id=message.from_user.id,
            )

            await message.answer(
                GENERATED_QUESTIONS
            )

            question = await interview_service.start_interview(
                session=session,
                user_id=user.id,
                difficulty=difficulty,
                position=position,
                requirements=requirements,
                max_questions=5,
            )

    except InvalidInterviewRequestError as e:
        await state.set_state(
            InterviewStates.waiting_position
        )

        await message.answer(
            str(e)
        )

        await message.answer(
            'Введите данные должности заново.'
        )
        return

    await state.set_state(
        InterviewStates.answering
    )

    await state.update_data(
        interview_id=question.interview_id
    )

    await message.answer(
        'Собеседование началось.\n\n'
        f'Должность: {position}\n\n'
        'Первый вопрос:\n'
        f'{question.question_text}',
        reply_markup=INTERVIEW_KEYBOARD,
    )