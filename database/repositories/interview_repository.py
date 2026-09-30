from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.interview import Interview
from database.models.interview_question import InterviewQuestion
from database.enums import Difficulty, InterviewStatus


class InterviewRepository:
    """Предоставляет методы для работы с сущностью Interview в базе данных."""

    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        difficulty: Difficulty,
        position: str,
        requirements: str,
        question_count: int | None
    ) -> Interview:
        """Создаёт новое собеседование в БД."""
        interview = Interview(
            user_id=user_id,
            difficulty=difficulty,
            position=position,
            requirements=requirements,
            question_count=question_count
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

    async def get_detail_by_id(
        self,
        session: AsyncSession,
        interview_id: int,
    ) -> Interview | None:
        """Возвращает собеседование с вопросами и ответами."""
        stmt = (
            select(Interview)
            .where(Interview.id == interview_id)
            .options(
                selectinload(Interview.user),
                selectinload(Interview.questions).selectinload(
                    InterviewQuestion.answer
                ),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list_recent(
        self,
        session: AsyncSession,
        limit: int = 50,
    ) -> list[Interview]:
        """Возвращает последние собеседования."""
        stmt = (
            select(Interview)
            .options(selectinload(Interview.user))
            .order_by(Interview.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id(
        self,
        session: AsyncSession,
        user_id: int
    ) -> list[Interview]:
        """
        Возвращает все законченные и прерванные
        собеседования по ID пользователя.
        """
        stmt = select(Interview).where(
            Interview.user_id == user_id,
            Interview.status != InterviewStatus.IN_PROGRESS
        )
        result = await session.execute(stmt)
        return result.scalars().all()

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

    async def get_history_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> list[Interview]:
        """Возвращает историю собеседований пользоваетля."""

        stmt = (
            select(Interview).where(
                Interview.user_id == user_id,
                Interview.status != InterviewStatus.IN_PROGRESS
            ).order_by(Interview.completed_at.desc()).limit(limit)
        )

        result = await session.execute(stmt)

        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        interview: Interview
    ) -> None:
        """Обновляет данные собеседования в БД."""
        session.add(interview)

    async def count_by_user_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """Считает все собеседования пользователя."""
        stmt = (
            select(func.count())
            .select_from(Interview)
            .where(Interview.user_id == user_id)
        )
        result = await session.execute(stmt)
        return int(result.scalar_one())

    async def count_created_in_period(
        self,
        session: AsyncSession,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        """Считает собеседования пользователя, созданные в указанном периоде."""
        stmt = (
            select(func.count())
            .select_from(Interview)
            .where(
                Interview.user_id == user_id,
                Interview.created_at >= period_start,
                Interview.created_at < period_end,
            )
        )
        result = await session.execute(stmt)
        return int(result.scalar_one())


interview_repository = InterviewRepository()
