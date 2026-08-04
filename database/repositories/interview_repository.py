from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.interview import Interview
from database.enums import Difficulty, InterviewStatus


class InterviewRepository:
    """Предоставляет методы для работы с сущностью Interview в базе данных."""
    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        difficulty: Difficulty,
        max_questions: int
    ) -> Interview:
        """Создаёт новое собеседование в БД."""
        interview = Interview(
            user_id=user_id,
            difficulty=difficulty,
            max_questions=max_questions
        )
        session.add(interview)
        return interview

    async def get_by_id(
        self,
        session: AsyncSession,
        interview_id: int,
    ) -> Interview | None:
        """Ищет собеседование в БД по ID."""
        stmt = select(Interview).where(Interview.id == interview_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_active_by_user_id(
        self,
        session: AsyncSession,
        user_id: int
    ) -> Interview | None:
        """Ищет активное собеседование пользователя по его ID."""
        stmt = select(Interview).where(
            Interview.user_id == user_id,
            Interview.status == InterviewStatus.IN_PROGRESS,
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def update(
        self,
        session: AsyncSession,
        interview: Interview
    ) -> None:
        """Обновляет данные собеседования в БД."""
        session.add(interview)
