from aiogram.types import LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from constants.subscription import (
    PREMIUM_DURATION_DAYS,
    PREMIUM_PRODUCT_PAYLOAD,
    PREMIUM_TITLE,
)
from database.models import User
from database.models.payment import PaymentStatus
from database.repositories.payment_repository import payment_repository
from services.subscription_service import subscription_service


class PaymentService:
    """Сервис оплаты PREMIUM через Telegram Payments / Stars."""

    def build_payload(self, user_id: int) -> str:
        """Формирует payload инвойса с id пользователя."""
        return f'{PREMIUM_PRODUCT_PAYLOAD}:{user_id}'

    def parse_user_id(self, payload: str) -> int | None:
        """Достаёт user_id из payload инвойса."""
        prefix = f'{PREMIUM_PRODUCT_PAYLOAD}:'
        if not payload.startswith(prefix):
            return None
        raw_id = payload.removeprefix(prefix)
        if not raw_id.isdigit():
            return None
        return int(raw_id)

    def get_invoice_prices(self) -> list[LabeledPrice]:
        """Цены для инвойса Telegram."""
        return [
            LabeledPrice(
                label=f'{PREMIUM_TITLE} на {PREMIUM_DURATION_DAYS} дней',
                amount=settings.premium_price_stars,
            )
        ]

    def get_provider_token(self) -> str:
        """Токен провайдера: пустой для Stars."""
        if settings.payment_currency.upper() == 'XTR':
            return ''
        return settings.payment_provider_token

    def format_price_text(self) -> str:
        """Человекочитаемая цена для сообщений бота."""
        if settings.payment_currency.upper() == 'XTR':
            return f'{settings.premium_price_stars} ⭐'
        return f'{settings.premium_price_stars} {settings.payment_currency}'

    async def create_pending_payment(
        self,
        session: AsyncSession,
        user: User,
    ) -> None:
        """Создаёт pending-запись перед отправкой инвойса."""
        await payment_repository.create(
            session=session,
            user_id=user.id,
            currency=settings.payment_currency.upper(),
            total_amount=settings.premium_price_stars,
            payload=self.build_payload(user.id),
            status=PaymentStatus.PENDING,
        )
        await session.commit()

    async def complete_premium_payment(
        self,
        session: AsyncSession,
        user: User,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str | None,
        currency: str,
        total_amount: int,
        payload: str,
    ) -> User:
        """Подтверждает оплату и активирует/продлевает PREMIUM."""
        existing = await payment_repository.get_by_telegram_charge_id(
            session=session,
            telegram_payment_charge_id=telegram_payment_charge_id,
        )
        if existing is not None:
            return user

        payment = await payment_repository.create(
            session=session,
            user_id=user.id,
            currency=currency,
            total_amount=total_amount,
            payload=payload,
            status=PaymentStatus.PENDING,
        )
        await payment_repository.mark_success(
            session=session,
            payment=payment,
            telegram_payment_charge_id=telegram_payment_charge_id,
            provider_payment_charge_id=provider_payment_charge_id,
        )
        subscription_service.activate_premium(user)
        await session.commit()
        return user


payment_service = PaymentService()
