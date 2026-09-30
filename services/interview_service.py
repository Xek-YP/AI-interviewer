from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.interview_repository import interview_repository
from database.repositories.interview_question_repository import interview_question_repository
from database.repositories.user_answer_repository import user_answer_repository
from database.models import InterviewQuestion, UserAnswer, Interview, User
from database.enums import Difficulty, InterviewStatus
from exceptions import (
    AlreadyAnsweredError,
    QuestionNotFoundError,
    InterviewNotFoundOrInterraptedError,
    InterviewIsCompletedError,
    InvalidInterviewRequestError,
    LLMServiceError,
    NoAnswerError
)
from schemas.answer import SubmitAnswerResult
from schemas.interview import InterviewEvaluation
from .llm_service import llm_service
from .subscription_service import subscription_service


class InterviewService:
    """Сервис работы с собеседованием."""

    async def _create_questions_pool(
        self,
        session: AsyncSession,
        interview_id: int,
        difficulty: Difficulty,
        position: str,
        requirements: str,
        max_questions: int
    ) -> list[InterviewQuestion]:
        """Генерирует и сохраняет пул вопросов для собеседования."""
        questions = await llm_service.generate_question_pool(
            difficulty=difficulty,
            position=position,
            requirements=requirements,
            max_questions=max_questions
        )
        return await interview_question_repository.bulk_create(
            session=session,
            interview_id=interview_id,
            questions=questions.questions
        )

    def _format_evaluation_items(self, items: list[str]) -> str:
        """Преобразует списки в строки."""
        return "\n".join(f"• {item}" for item in items)

    def _format_answers_for_evaluation(
        self,
        answers: list[UserAnswer]
    ) -> str:
        """Преобразует список ответов пользователя в понятный текст."""
        result = []

        for index, answer in enumerate(answers, start=1):
            result.append(
                f"""
                    Вопрос {index}:
                    {answer.question.question_text}

                    Ответ кандидата:
                    {answer.answer_text}

                    Оценка:
                    {answer.score}

                    Сильные стороны:
                    {answer.strengths}

                    Слабые стороны:
                    {answer.weaknesses}
                """
            )
        return '\n'.join(result)

    def _calculate_interview_score(
        self,
        answers: list[UserAnswer],
    ) -> int:
        """Рассчитывает итоговую оценку за собеседование."""
        if not answers:
            return 0
        return round(sum(answer.score for answer in answers)/len(answers))

    async def get_active_question_for_resume(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> InterviewQuestion | None:
        """Возвращает текущий неотвеченный вопрос активного интервью."""
        interview = await interview_repository.get_active_by_user_id(
            session=session,
            user_id=user_id,
        )
        if not interview:
            return None

        return await interview_question_repository.get_unanswered_by_interview_id(
            session=session,
            interview_id=interview.id,
        )

    async def start_interview(
        self,
        session: AsyncSession,
        user: User,
        difficulty: Difficulty,
        position: str,
        requirements: str,
        max_questions: int
    ) -> InterviewQuestion:
        """Создаёт собеседование и пул вопросов в БД, возвращает 1 вопрос."""
        try:
            await subscription_service.ensure_can_start_interview(
                session=session,
                user=user,
            )

            validation = await llm_service.validate_interview_request(
                position=position,
                requirements=requirements
            )

            if not validation.valid:
                raise InvalidInterviewRequestError(validation.reason)

            active_interview = await interview_repository.get_active_by_user_id(
                session=session,
                user_id=user.id
            )

            if active_interview:
                active_interview.status = InterviewStatus.INTERRUPTED
                active_interview.completed_at = datetime.now(timezone.utc)
                await interview_repository.update(
                    session=session, interview=active_interview
                )

            interview = await interview_repository.create(
                session=session,
                user_id=user.id,
                difficulty=difficulty,
                position=position,
                requirements=requirements,
                question_count=None,
            )
            await session.flush()

            questions = await self._create_questions_pool(
                session=session,
                interview_id=interview.id,
                difficulty=difficulty,
                position=position,
                requirements=requirements,
                max_questions=max_questions
            )
            if not questions:
                raise LLMServiceError('LLM не сгенерировала ни одного вопроса.')
            interview.question_count = len(questions)
            await session.commit()

            return questions[0]

        except Exception:
            await session.rollback()
            raise

    async def submit_answer(
        self,
        session: AsyncSession,
        telegram_id: int,
        answer_text: str,
    ) -> SubmitAnswerResult:
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

            llm_answer = await llm_service.evaluate_answer(
                question=question.question_text,
                answer=answer_text,
                position=interview.position,
                requirements=interview.requirements,
                difficulty=question.difficulty,
                category=question.category,
            )

            user_answer = await user_answer_repository.create(
                session=session,
                interview_question_id=question.id,
                answer_text=answer_text,
                score=llm_answer.score,
                strengths=self._format_evaluation_items(llm_answer.strengths),
                weaknesses=self._format_evaluation_items(llm_answer.weaknesses),
                confidence=llm_answer.confidence
            )

            await session.flush()

            next_question = await interview_question_repository.get_current_question(
                session=session,
                telegram_id=telegram_id
            )

            if next_question:
                await session.commit()
                return SubmitAnswerResult(
                    next_question=next_question,
                    user_answer=user_answer,
                    evaluation=None
                )

            evaluation = await self.finish_interview(
                session=session,
                interview=interview
            )
            await session.commit()

            return SubmitAnswerResult(
                next_question=None,
                user_answer=user_answer,
                evaluation=evaluation
            )

        except Exception:
            await session.rollback()
            raise

    async def finish_interview(
        self,
        session: AsyncSession,
        interview: Interview
    ) -> InterviewEvaluation:
        """Завершает собеседование."""

        answers = await user_answer_repository.get_all_by_interview_id(
            session=session,
            interview_id=interview.id,
        )
        if not answers:
            raise NoAnswerError(
                'Нельзя завершить собеседование без ответов.'
            )

        formatted_answers = self._format_answers_for_evaluation(
            answers=answers
        )

        evalaution = await llm_service.evaluate_interview(
            position=interview.position,
            requirements=interview.requirements,
            difficulty=interview.difficulty,
            answers=formatted_answers
        )
        interview.score = evalaution.score
        interview.summary = evalaution.summary
        interview.strengths = self._format_evaluation_items(evalaution.strengths)
        interview.weaknesses = self._format_evaluation_items(evalaution.weaknesses)
        interview.recommendation = evalaution.recommendation
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.now(timezone.utc)
        await session.flush()
        return evalaution

    async def get_history(
        self,
        session: AsyncSession,
        user_id: int
    ) -> list[Interview]:
        """Возвращает список собеседований пользователя."""

        return await interview_repository.get_history_by_user_id(
            session=session,
            user_id=user_id
        )

    async def get_statistics(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> dict[str, int | float]:
        """Возвращает общую статистику собеседований пользователя."""

        interviews = await self.get_history(
            session=session,
            user_id=user_id
        )
        if not interviews:
            return {
                'completed_count': 0,
                'average_score': 0,
                'best_score': 0
            }

        scores = [
            interview.score
            for interview in interviews
            if interview.score is not None
        ]

        if not scores:
            return {
                'completed_count': len(interviews),
                'average_score': 0,
                'best_score': 0
            }

        return {
            'completed_count': len(interviews),
            'average_score': round(sum(scores) / len(scores)),
            'best_score': max(scores)
        }
        
    async def interrupted_interview(
        self,
        session: AsyncSession,
        user_id: int
    ) -> None:
        """Завершает начатое собеседование."""

        interview = await interview_repository.get_active_by_user_id(
            session=session,
            user_id=user_id
        )
        if not interview:
            raise InterviewNotFoundOrInterraptedError(
                'Собеседование не найдено или уже закончено.'
            )
        interview.status = InterviewStatus.INTERRUPTED
        interview.completed_at = datetime.now(timezone.utc)

        await session.commit()


        
        
        
interview_service = InterviewService()
