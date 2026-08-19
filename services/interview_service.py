from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.interview_repository import interview_repository
from database.repositories.interview_question_repository import interview_question_repository
from database.repositories.question_category_repository import question_category_repository
from database.repositories.user_answer_repository import user_answer_repository
from database.models import InterviewQuestion, QuestionCategory, UserAnswer
from database.enums import Difficulty, InterviewStatus
from exceptions import (
    AlreadyAnsweredError,
    NoActiveCategoriesError,
    QuestionNotFoundError,
    InterviewNotFoundOrInterraptedError,
    InterviewIsCompletedError
)
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

    def _format_evaluation_items(self, items: list[str]) -> str:
        """Преобразует списки в строки."""
        return "\n".join(f"• {item}" for item in items)

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

    async def submit_answer(
        self,
        session: AsyncSession,
        telegram_id: int,
        answer_text: str,
    ) -> tuple[InterviewQuestion | None, UserAnswer]:
        """Сохраняет ответ пользователя и либо возвращает следующий вопрос либо None."""
        try:
            question = await interview_question_repository.get_current_question(
                session=session,
                telegram_id=telegram_id
            )

            if not question:
                raise QuestionNotFoundError(
                    'Вопрос на который отвечает пользователь не найден.'
                )

            interview = await interview_repository.get_by_id(
                session=session,
                interview_id=question.interview_id
            )

            if not interview or interview.status == InterviewStatus.INTERRUPTED:
                raise InterviewNotFoundOrInterraptedError(
                    'Собеседование не найдено или прервано.'
                )
            elif interview.status == InterviewStatus.COMPLETED:
                raise InterviewIsCompletedError('Собеседование закончено.')

            if await user_answer_repository.get_by_question_id(
                session=session,
                question_id=question.id
            ):
                raise AlreadyAnsweredError(
                    'На данный вопрос уже был получен ответ.'
                )

            next_category = await question_category_repository.get_random_category(
                session
            )
            if not next_category:
                raise NoActiveCategoriesError('Нет активных категорий.')

            llm_answer = await llm_service.evaluate_answer(
                question=question.question_text,
                answer=answer_text,
                difficulty=question.difficulty,
                category=question.category.name,
            )

            user_answer = await user_answer_repository.create(
                session=session,
                interview_question_id=question.id,
                recommended_category_id=next_category.id,
                answer_text=answer_text,
                score=llm_answer.score,
                strengths=self._format_evaluation_items(llm_answer.strengths),
                weaknesses=self._format_evaluation_items(llm_answer.weaknesses),
                recommended_difficulty=llm_answer.recommended_difficulty,
                confidence=llm_answer.confidence
            )

            if question.order_number < interview.max_questions:
                next_question = await self._generate_question(
                    session=session,
                    interview_id=interview.id,
                    question_category=next_category,
                    difficulty=llm_answer.recommended_difficulty,
                    order_number=question.order_number + 1
                )

            else:
                interview.status = InterviewStatus.COMPLETED
                next_question = None
                interview.completed_at = datetime.now(timezone.utc)

            await session.commit()

            return next_question, user_answer

        except Exception:
            await session.rollback()
            raise

interview_service = InterviewService()