from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime, Enum,
    ForeignKey, Text,
    Integer, SmallInteger, String,
    UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base
from database.enums import Difficulty


if TYPE_CHECKING:
    from database.models import Interview, UserAnswer

class InterviewQuestion(Base):
    """Модель вопросов, заданных непосредственно во время собеседования."""
    __tablename__ = 'interview_questions'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    interview_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('interviews.id'),
        name='fk_interview_questions_interview_id_interview',
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty),
        nullable=False
    )
    order_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    interview: Mapped['Interview'] = relationship(
        'Interview',
        back_populates='questions'
    )
    answer: Mapped['UserAnswer'] = relationship(
        'UserAnswer',
        back_populates='question',
        uselist=False
    )

    __table_args__ = (
        UniqueConstraint(
            'fk_interview_questions_interview_id_interview', 'order_number',
            name='uq_interview_order_number'
        ),
    )
