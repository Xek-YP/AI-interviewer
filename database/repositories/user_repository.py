from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        """Создаёт нового пользователея в БД."""
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
