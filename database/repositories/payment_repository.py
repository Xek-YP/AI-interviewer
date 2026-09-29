from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.payment import Payment, PaymentStatus


class PaymentRepository:
    """Репозиторий платежей."""

    async def create(
        self,
        session: AsyncSession,
        user_id: int,
        currency: str,
        total_amount: int,
        payload: str,
        status: PaymentStatus = PaymentStatus.PENDING,
    ) -> Payment:
        """Создаёт запись о платеже."""
        payment = Payment(
            user_id=user_id,
            currency=currency,
            total_amount=total_amount,
            payload=payload,
            status=status,
        )
        session.add(payment)
        return payment

    async def get_by_telegram_charge_id(
        self,
        session: AsyncSession,
        telegram_payment_charge_id: str,
    ) -> Payment | None:
        """Ищет платёж по telegram charge id."""
        stmt = select(Payment).where(
            Payment.telegram_payment_charge_id == telegram_payment_charge_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def mark_success(
        self,
        session: AsyncSession,
        payment: Payment,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str | None,
    ) -> Payment:
        """Помечает платёж успешным."""
        payment.status = PaymentStatus.SUCCESS
        payment.telegram_payment_charge_id = telegram_payment_charge_id
        payment.provider_payment_charge_id = provider_payment_charge_id
        session.add(payment)
        return payment


payment_repository = PaymentRepository()
