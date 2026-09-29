from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.buttons_text import VIEW_HISTORY

from database.session import AsyncSessionLocal
from services.interview_service import interview_service
from services.user_service import user_service


router = Router()


@router.message(F.text == VIEW_HISTORY)
async def history_handler(
    message: Message,
):
    """Показывает историю завершённых собеседований."""

    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.get_user(
            session=session,
            telegram_id=message.from_user.id,
        )

        interviews = await interview_service.get_history(
            session=session,
            user_id=user.id,
        )

    if not interviews:
        await message.answer(
            'У вас пока нет завершенных собеседований.'
        )
        return

    response = '📚 История собеседований:\n\n'

    for interview in interviews:
        response += (
            f'📝 {interview.position}\n'
            f'📅 {interview.completed_at:%d.%m.%Y}\n'
            f'⭐ Оценка: {interview.score}/100\n'
            f'🎯 Рекомендация: '
            f'{interview.recommendation}\n\n'
        )

    await message.answer(response)
