from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.question_category import QuestionCategory


class QuestionCategoryRepository:
    """
    Предоставляет методы для работы с сущностью
    QuestionCategory в базе данных.
    """
    async def create(
        self,
        session: AsyncSession,
        name: str,
    ) -> QuestionCategory:
        """Создаёт новую категорию в БД."""
        question_category = QuestionCategory(name=name)
        session.add(question_category)
        return question_category

    async def get_by_id(
        self,
        session: AsyncSession,
        category_id: int
    ) -> QuestionCategory | None:
        """Ищет категорию в БД по ID."""
        stmt = select(QuestionCategory).where(
            QuestionCategory.id == category_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_name(
        self,
        session: AsyncSession,
        category_name: str,
    ) -> QuestionCategory | None:
        """Ищет категорию в БД по названию."""
        stmt = select(QuestionCategory).where(
            QuestionCategory.name == category_name
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        session: AsyncSession
    ) -> list[QuestionCategory]:
        """Возвращает все категории."""
        stmt = select(QuestionCategory)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_all_active(
        self,
        session: AsyncSession
    ) -> list[QuestionCategory]:
        """Ищет все активные категории в БД."""
        stmt = select(QuestionCategory).where(
            QuestionCategory.is_active.is_(True)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_random_category(
        self,
        session: AsyncSession,
    ) -> QuestionCategory | None:
        """Возвращает случайную активную категорию."""
        stmt = select(QuestionCategory).where(
            QuestionCategory.is_active.is_(True)
        ).order_by(func.random()).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def update(
        self,
        session: AsyncSession,
        question_category: QuestionCategory,
    ) -> None:
        """Добавляет обновленные данные категории в текущую сессию."""
        session.add(question_category)

question_category_repository = QuestionCategoryRepository()
