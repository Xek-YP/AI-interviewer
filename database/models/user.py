from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BIGINT, DateTime, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base

if TYPE_CHECKING:
    from database.models import Interview

class User(Base):
    """Модель пользователя."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    telegram_id: Mapped[int] = mapped_column(
        BIGINT,
        unique=True,
        nullable=False
    )
    username: Mapped[None | str] = mapped_column(
        String(32),
        nullable=True
    )
    first_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    interviews: Mapped[list['Interview']] = relationship(
        'Interview', back_populates='user'
    )
