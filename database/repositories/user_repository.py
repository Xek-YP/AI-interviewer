from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User

class UserRepository:
    async def get_user_by_telegram_id(
        self,
        telegram_id: int,
        session: AsyncSession
    ) -> User | None:
        """Функция возвращает пользователя из БД если такой существует."""
        stmt = select(User).where(User.telegram_id==telegram_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        session: AsyncSession,
        telegram_id: int,
        username: str | None,
    ) -> User:
        """Функция добавления новых пользователей в БД."""
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update_last_activity(
        self,
        session: AsyncSession,
        telegram_id: int
    ) -> None:
        """Функция обновляющая последнюю активность пользователя."""
        user = await self.get_user_by_telegram_id(
            telegram_id=telegram_id,
            session=session
        )
        if user:
            user.last_activity_at = datetime.now(timezone.utc)
            await session.commit()
        else:
            raise ValueError('Пользователь с таким id отсутствует.')
