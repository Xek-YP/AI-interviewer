from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import InterviewQuestion, UserAnswer
from database.enums import Difficulty
from database.repositories.user_repository import user_repository
from database.repositories.interview_repository import interview_repository
from exceptions.interview_exception import InterviewNotFoundOrInterraptedError


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

    async def get_unanswered_by_interview_id(
        self,
        session: AsyncSession,
        interview_id: int
    ) -> InterviewQuestion | None:
        stmt = (
            select(InterviewQuestion).outerjoin(
                UserAnswer,
                UserAnswer.interview_question_id == InterviewQuestion.id,
            ).where(
                InterviewQuestion.interview_id == interview_id,
                UserAnswer.id.is_(None),
            ).order_by(InterviewQuestion.order_number).options(
                joinedload(InterviewQuestion.category)
            ).limit(1)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_current_question(
        self,
        session: AsyncSession,
        telegram_id: int,
    ) -> InterviewQuestion:
        user = await user_repository.get_by_telegram_id(
            session=session,
            telegram_id=telegram_id
        )

        interview = await interview_repository.get_active_by_user_id(
            session=session,
            user_id=user.id
        )

        if not interview:
            raise InterviewNotFoundOrInterraptedError(
                'Не найдено активных собеседований.'
            )

        questions = await self.get_unanswered_by_interview_id(
            session=session,
            interview_id=interview.id
        )

        return questions

interview_question_repository = InterviewQuestionRepository()
