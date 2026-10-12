from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.interview import resume_active_interview_if_any
from bot.handlers.messages import GENERATED_QUESTIONS
from bot.handlers.start import MAIN_KEYBOARD
from bot.keyboards.buttons_text import (
    DIFFICULTY_BUTTONS,
    START_INTERVIEW,
)
from bot.keyboards.difficulty_keyboard import create_difficulty_keyboard
from bot.keyboards.interview_keyboard import create_interview_keyboard
from bot.keyboards.payment_keyboard import create_buy_premium_keyboard
from bot.states.interview import InterviewStates
from constants.subscription import TEXT_ONLY_HINT
from database.session import AsyncSessionLocal
from exceptions import (
    InterviewLimitExceededError,
    InvalidInterviewRequestError,
)
from services.interview_service import interview_service
from services.subscription_service import subscription_service
from services.user_service import user_service


router = Router()

DIFFICULTY_KEYBOARD = create_difficulty_keyboard()
INTERVIEW_KEYBOARD = create_interview_keyboard()


@router.message(F.text == START_INTERVIEW)
async def start_interview_handler(
    message: Message,
    state: FSMContext,
):
    """Запуск создания интервью или продолжение активного."""
    if message.from_user is None:
        return

    current_state = await state.get_state()
    if current_state == InterviewStates.answering.state:
        await message.answer(
            'Сейчас уже идёт собеседование.\n'
            'Завершите его или ответьте на текущий вопрос.',
            reply_markup=INTERVIEW_KEYBOARD,
        )
        return

    try:
        async with AsyncSessionLocal() as session:
            user = await user_service.get_user(
                session=session,
                telegram_id=message.from_user.id,
            )
            user_id = user.id

        if await resume_active_interview_if_any(
            message=message,
            state=state,
            user_id=user_id,
        ):
            return

        async with AsyncSessionLocal() as session:
            user = await user_service.get_user(
                session=session,
                telegram_id=message.from_user.id,
            )
            await subscription_service.ensure_can_start_interview(
                session=session,
                user=user,
            )
    except InterviewLimitExceededError as e:
        await state.clear()
        await message.answer(
            str(e),
            reply_markup=create_buy_premium_keyboard(),
        )
        return

    await state.set_state(InterviewStates.waiting_position)
    await message.answer(
        'Введите название должности, на которую хотите пройти собеседование.',
        reply_markup=MAIN_KEYBOARD,
    )


@router.message(InterviewStates.waiting_position, ~F.text)
@router.message(InterviewStates.waiting_requirements, ~F.text)
@router.message(InterviewStates.waiting_difficulty, ~F.text)
async def non_text_during_setup(message: Message):
    """Просит прислать текст на этапе настройки."""
    await message.answer(TEXT_ONLY_HINT)


@router.message(InterviewStates.waiting_position, F.text)
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

    await state.update_data(position=position)
    await state.set_state(InterviewStates.waiting_requirements)
    await message.answer(
        'Теперь отправьте требования вакансии.\n\n'
        'Например:\n'
        'Python, Django, PostgreSQL, Redis, Docker.'
    )


@router.message(InterviewStates.waiting_requirements, F.text)
async def requirements_handler(
    message: Message,
    state: FSMContext,
):
    """Получение требований вакансии."""
    if not message.text:
        return

    requirements = message.text.strip()
    if len(requirements) < 15:
        await message.answer('Введите больше информации о вакансии.')
        return

    await state.update_data(requirements=requirements)
    await state.set_state(InterviewStates.waiting_difficulty)
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
    if message.from_user is None or not message.text:
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
            await message.answer(GENERATED_QUESTIONS)
            question = await interview_service.start_interview(
                session=session,
                user=user,
                difficulty=difficulty,
                position=position,
                requirements=requirements,
                max_questions=11,
            )
    except InvalidInterviewRequestError as e:
        await state.clear()
        await state.set_state(InterviewStates.waiting_position)
        await message.answer(str(e))
        await message.answer(
            'Введите название должности заново.',
            reply_markup=MAIN_KEYBOARD,
        )
        return
    except InterviewLimitExceededError as e:
        await state.clear()
        await message.answer(
            str(e),
            reply_markup=create_buy_premium_keyboard(),
        )
        await message.answer(
            'Вернуться в меню:',
            reply_markup=MAIN_KEYBOARD,
        )
        return
    except Exception:
        await state.clear()
        await message.answer(
            'Не удалось создать собеседование. Попробуйте начать заново.',
            reply_markup=MAIN_KEYBOARD,
        )
        raise

    await state.set_state(InterviewStates.answering)
    await state.update_data(interview_id=question.interview_id)
    await message.answer(
        'Собеседование началось.\n\n'
        f'Должность: {position}\n\n'
        'Первый вопрос:\n'
        f'{question.question_text}',
        reply_markup=INTERVIEW_KEYBOARD,
    )
