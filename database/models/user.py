from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BIGINT, Boolean, DateTime, Integer, String, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database.models.base import Base
from database.enums import SubscriptionType

if TYPE_CHECKING:
    from database.models import Interview, Payment

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
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType),
        default=SubscriptionType.FREE,
        nullable=False
    )
    subscription_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default='false',
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
    payments: Mapped[list['Payment']] = relationship(
        'Payment', back_populates='user'
    )
