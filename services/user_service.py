from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repository import user_repository
from database.models import User
from exceptions import UserBlockedError


class UserService:
    """Сервис работы с пользователями."""

    async def register_user(
        self,
        session: AsyncSession,
        telegram_id: int,
        first_name: str,
        username: str | None = None,
    ) -> User:
        """
        Регистрирует новых пользователей
        или обновляет последнюю активность
        уже существующим пользователям.
        """
        user = await user_repository.get_by_telegram_id(
            telegram_id=telegram_id,
            session=session
        )
        if user:
            if user.is_blocked:
                raise UserBlockedError(
                    'Ваш аккаунт заблокирован. Обратитесь к администратору.'
                )
            user.username = username
            user.first_name = first_name
            user.last_activity_at = datetime.now(timezone.utc)
        else:
            user = await user_repository.create(
                session=session,
                telegram_id=telegram_id,
                first_name=first_name,
                username=username
            )
            await session.flush()
        await session.commit()
        return user

    async def get_user(
        self,
        session: AsyncSession,
        telegram_id: int
    ) -> User:
        """Возвращает пользователя по telegram_id."""
        user = await user_repository.get_by_telegram_id(
            telegram_id=telegram_id,
            session=session
        )
        if not user:
            raise ValueError('Пользователя с таким telegram_id нет.')
        if user.is_blocked:
            raise UserBlockedError(
                'Ваш аккаунт заблокирован. Обратитесь к администратору.'
            )
        return user


user_service = UserService()
