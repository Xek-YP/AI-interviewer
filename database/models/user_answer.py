from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, DateTime, Enum,
    ForeignKey, Float, Text,
    Integer, SmallInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base
from database.enums import Difficulty


if TYPE_CHECKING:
    from database.models import InterviewQuestion

class UserAnswer(Base):
    """Модель ответов пользователей."""
    __tablename__ = 'user_answers'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    interview_question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('interview_questions.id'),
        name='fk_user_answers_interview_question_id_interview_questions',
        nullable=False,
    )
    answer_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )
    strengths: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    weaknesses: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    question: Mapped['InterviewQuestion'] = relationship(
        'InterviewQuestion',
        back_populates='answer',
        uselist=False
    )

    __table_args__ = (
        CheckConstraint(
            'score >= 0 and score <=100',
            name='ck_score_from_0_to_100'
        ),
        UniqueConstraint(
            'fk_user_answers_interview_question_id_interview_questions',
            name='uq_user_answers_interview_question_id'
        ),
    )
