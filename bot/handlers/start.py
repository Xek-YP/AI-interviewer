from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import bot.handlers.messages as handlers_text
from bot.keyboards.interview_keyboard import create_interview_keyboard
from bot.keyboards.main_keyboard import (
    create_main_keyboard,
    create_onboarding_keyboard,
)
from bot.states.interview import InterviewStates
from constants.subscription import FREE_MONTHLY_INTERVIEW_LIMIT
from database.repositories.interview_repository import interview_repository
from database.session import AsyncSessionLocal
from services.interview_service import interview_service
from services.payment_service import payment_service
from services.subscription_service import subscription_service
from services.user_service import user_service


router = Router()

MAIN_KEYBOARD = create_main_keyboard()
ONBOARDING_KEYBOARD = create_onboarding_keyboard()
INTERVIEW_KEYBOARD = create_interview_keyboard()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Регистрация/приветствие и восстановление активного интервью."""
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.register_user(
            session=session,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )
        await subscription_service.sync_subscription_status(
            session=session,
            user=user,
        )
        active_question = await interview_service.get_active_question_for_resume(
            session=session,
            user_id=user.id,
        )
        started_count = await interview_repository.count_by_user_id(
            session=session,
            user_id=user.id,
        )
        premium_active = subscription_service.is_premium_active(user)
        premium_expires_at = (
            subscription_service.get_premium_expires_at(user)
            if premium_active
            else None
        )

    if active_question is not None:
        await state.set_state(InterviewStates.answering)
        await state.update_data(interview_id=active_question.interview_id)
        await message.answer(
            handlers_text.RESUME_INTERVIEW_MESSAGE.format(
                question=active_question.question_text
            ),
            reply_markup=INTERVIEW_KEYBOARD,
        )
        return

    await state.clear()
    if premium_expires_at is not None:
        tariff_block = handlers_text.build_premium_tariff_block(
            premium_expires_at.strftime('%d.%m.%Y'),
        )
    else:
        tariff_block = handlers_text.build_free_tariff_block(
            price_label=payment_service.format_monthly_price_text(),
            free_limit=FREE_MONTHLY_INTERVIEW_LIMIT,
        )

    show_menu = started_count > 0 or premium_active
    await message.answer(
        handlers_text.build_onboarding_message(tariff_block),
        reply_markup=MAIN_KEYBOARD if show_menu else ONBOARDING_KEYBOARD,
    )
