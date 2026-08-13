from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import (
    interview_repository,
    interview_question_repository,
    question_category_repository
)
from database.models import InterviewQuestion, QuestionCategory
from database.enums import Difficulty, InterviewStatus
from exceptions.category_exception import NoActiveCategoriesError
from .llm_service import llm_service


class InterviewService:
    """Сервис работы с собеседовнаием."""

    async def _generate_question(
        self,
        session: AsyncSession,
        interview_id: int,
        question_category: QuestionCategory,
        difficulty: Difficulty,
        order_number: int
    ) -> InterviewQuestion:
        """Создаёт и возвращает вопрос по заданной категории и сложности."""
        question_text = await llm_service.generate_question(
            difficulty=difficulty,
            category=question_category.name
        )
        return await interview_question_repository.create(
            session=session, interview_id=interview_id,
            question_category_id=question_category.id,
            question_text=question_text,
            difficulty=difficulty, order_number=order_number
        )
        
    async def start_interview(
        self,
        session: AsyncSession,
        user_id: int,
        difficulty: Difficulty,
        max_questions: int
    ) -> InterviewQuestion:
        """Создаёт собеседование в БД и возвращает 1 вопрос."""
        try:
            question_category=await question_category_repository.get_random_category(
                session
            )
            if not question_category:
                raise NoActiveCategoriesError('Нет активных категорий.')
            active_interview = await interview_repository.get_active_by_user_id(
                session=session,
                user_id=user_id
            )
            if active_interview:
                active_interview.status = InterviewStatus.INTERRUPTED
                active_interview.completed_at = datetime.now(timezone.utc)
                await interview_repository.update(
                    session=session, interview=active_interview
                )
            interview = await interview_repository.create(
                session=session, user_id=user_id,
                difficulty=difficulty, max_questions=max_questions
            )
            await session.flush()
            question = await self._generate_question(
                session=session, interview_id=interview.id,
                question_category=question_category, difficulty=difficulty,
                order_number=1
            )
            await session.commit()
            return question
        except Exception:
            await session.rollback()
            raise

interview_service = InterviewService()