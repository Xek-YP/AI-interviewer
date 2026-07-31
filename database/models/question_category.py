from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base


if TYPE_CHECKING:
    from database.models import InterviewQuestion

class QuestionCategory(Base):
    """Модель категорий вопросов."""
    __tablename__ = 'question_categories'
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    questions: Mapped[list['InterviewQuestion']] = relationship(
        'InterviewQuestion',
        back_populates='category'
    )
