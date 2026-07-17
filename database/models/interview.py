from datetime import datetime

from sqlalchemy import (
    CheckConstraint, DateTime,
    Enum, ForeignKey,
    Integer, SmallInteger
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base
from database.enums import Difficulty, InterviewStatus


class Interview(Base):
    """Модель собеседования."""

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
        CheckConstraint(
            'score >= 0 and score <=100',
            name='ck_score_from_0_to_100'
        ),
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
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )