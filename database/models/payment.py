from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database.models.base import Base

if TYPE_CHECKING:
    from database.models import User


class PaymentStatus(StrEnum):
    """Статус платежа."""

    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'


class Payment(Base):
    """Модель платежа за PREMIUM."""

    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        nullable=False,
    )
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    provider_payment_charge_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )
    total_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    payload: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name='paymentstatus',
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    user: Mapped['User'] = relationship('User', back_populates='payments')
