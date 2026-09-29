from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.buttons_text import PROFILE

from database.session import AsyncSessionLocal
from services.interview_service import interview_service
from services.user_service import user_service


router = Router()


@router.message(F.text == PROFILE)
async def profile_handler(
    message: Message,
):
    """Показывает профиль пользователя."""

    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.get_user(
            session=session,
            telegram_id=message.from_user.id,
        )

        statistics = await interview_service.get_statistics(
            session=session,
            user_id=user.id,
        )

    username = (
        f'@{user.username}'
        if user.username
        else 'Не указан'
    )

    subscription = user.subscription_type.value.upper()

    response = (
        '👤 Профиль\n\n'
        f'Имя: {user.first_name}\n'
        f'Username: {username}\n'
        f'Дата регистрации: '
        f'{user.created_at:%d.%m.%Y}\n\n'
        f'💎 Подписка: {subscription}\n\n'
        '📊 Статистика\n'
        f'• Завершённых собеседований: '
        f'{statistics["completed_count"]}\n'
        f'• Средняя оценка: '
        f'{statistics["average_score"]}/100\n'
        f'• Лучший результат: '
        f'{statistics["best_score"]}/100'
    )

    await message.answer(response)
