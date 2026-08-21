from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import UserAnswer, InterviewQuestion
from database.enums import Difficulty


class UserAnswerRepository:
    """Предоставляет методы для работы с сущностью UserAnswer в базе данных."""
    async def create(
        self,
        session: AsyncSession,
        interview_question_id: int,
        recommended_category_id: int,
        answer_text: str,
        score: int,
        strengths: str,
        weaknesses: str,
        recommended_difficulty: Difficulty,
        confidence: float | None,
    ) -> UserAnswer:
        """Создаёт новый ответ к вопросу в БД."""
        user_answer = UserAnswer(
            interview_question_id=interview_question_id,
            recommended_category_id=recommended_category_id,
            answer_text=answer_text,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_difficulty=recommended_difficulty,
            confidence=confidence
        )
        session.add(user_answer)
        return user_answer

    async def get_by_id(
        self,
        session: AsyncSession,
        answer_id: int
    ) -> UserAnswer | None:
        """Возвращает ответ по ID."""
        stmt = select(UserAnswer).where(
            UserAnswer.id == answer_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_all_by_interview_id(
        self,
        session: AsyncSession,
        interview_id: int
    ) -> list[UserAnswer]:
        """Возвращает список ответов по id собеседования."""
        stmt = (
            select(UserAnswer)
            .join(InterviewQuestion, UserAnswer.interview_question_id == InterviewQuestion.id)
            .where(InterviewQuestion.interview_id == interview_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_question_id(
        self,
        session: AsyncSession,
        question_id: int,
    ) -> UserAnswer | None:
        """Возвращает ответ по ID вопроса."""
        stmt = select(UserAnswer).where(
            UserAnswer.interview_question_id == question_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

user_answer_repository = UserAnswerRepository()
