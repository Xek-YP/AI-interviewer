from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint, DateTime,
    Enum, ForeignKey,
    Integer, SmallInteger
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base
from database.enums import Difficulty, InterviewStatus


if TYPE_CHECKING:
    from database.models import User, InterviewQuestion

class Interview(Base):
    """Модель собеседования."""
    __tablename__ = 'interviews'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        name='fk_interview_user_id_user'
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(
            Difficulty,
        ),
    )
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(
            InterviewStatus,
        ),
        server_default=InterviewStatus.IN_PROGRESS,
    )
    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    max_questions: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    user: Mapped['User'] = relationship('User', back_populates='interviews')
    questions: Mapped[list['InterviewQuestion']] = relationship(
        'InterviewQuestion',
        back_populates='interview'
    )

    __table_args__ = (
        CheckConstraint(
            'score >= 0 and score <=100',
            name='ck_score_from_0_to_100'
        ),
    )