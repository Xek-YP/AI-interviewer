from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.interview_question import InterviewQuestion
from database.enums import Difficulty


class InterviewQuestionRepository:
    """
    Предоставляет методы для работы
    с сущностью InterviewQuestion в базе данных.
    """
    async def create(
        self,
        session: AsyncSession,
        interview_id: int,
        question_category_id: int,
        question_text: str,
        difficulty: Difficulty,
        order_number: int,
    ) -> InterviewQuestion:
        """Создаёт новый вопрос к собеседованию в БД."""
        interview_question = InterviewQuestion(
            interview_id=interview_id,
            question_category_id=question_category_id,
            question_text=question_text,
            difficulty=difficulty,
            order_number=order_number
        )
        session.add(interview_question)
        return interview_question

    async def get_by_id(
        self,
        session: AsyncSession,
        interview_question_id: int,
    ) -> InterviewQuestion | None:
        """Ищет вопрос в БД по ID."""
        stmt = select(InterviewQuestion).where(
            InterviewQuestion.id == interview_question_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_interview_and_order_number(
        self,
        session: AsyncSession,
        interview_id: int,
        order_number: int
    ) -> InterviewQuestion | None:
        """Возвращает вопрос по ID собеседования и номеру вопроса."""
        stmt = select(InterviewQuestion).where(
            InterviewQuestion.interview_id == interview_id,
            InterviewQuestion.order_number == order_number
        )
        result = await session.execute(stmt)
        return result.scalars().one_or_none()

    async def get_all_by_interview_id(
        self,
        session: AsyncSession,
        interview_id: int,
    ) -> list[InterviewQuestion]:
        """Возвращает все вопросы конкретного собеседования."""
        stmt = select(InterviewQuestion).where(
            InterviewQuestion.interview_id == interview_id
        )
        result = await session.execute(stmt)
        return result.scalars().all()