from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.user import User


class UserRepository:
    """Предоставляет методы для работы с сущностью User в базе данных."""

    async def create(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
        first_name: str
    ) -> User:
        """Создаёт нового пользователя в БД."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )
        session.add(user)
        return user

    async def get_by_telegram_id(
        self,
        telegram_id: int,
        session: AsyncSession
    ) -> User | None:
        """Ищет пользователя по телеграмм ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> User | None:
        """Ищет пользователя по ID."""
        return await session.get(User, user_id)

    async def list_users(
        self,
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Возвращает список пользователей."""
        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_interviews(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> User | None:
        """Возвращает пользователя с собеседованиями."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.interviews))
        )
        result = await session.execute(stmt)
        return result.scalars().first()


user_repository = UserRepository()
