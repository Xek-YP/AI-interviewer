from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from constants.subscription import (
    FREE_MONTHLY_INTERVIEW_LIMIT,
    PREMIUM_DURATION_DAYS,
)
from database.enums import SubscriptionType
from database.models import User
from database.repositories.interview_repository import interview_repository
from exceptions import InterviewLimitExceededError


class SubscriptionService:
    """Сервис работы с подпиской."""

    def _ensure_utc(self, value: datetime) -> datetime:
        """Приводит datetime к timezone-aware UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _now(self, now: datetime | None = None) -> datetime:
        """Возвращает текущее время в UTC."""
        return self._ensure_utc(now or datetime.now(timezone.utc))

    def get_premium_expires_at(self, user: User) -> datetime | None:
        """Возвращает дату окончания PREMIUM или None."""
        if user.subscription_started_at is None:
            return None
        started_at = self._ensure_utc(user.subscription_started_at)
        return started_at + timedelta(days=PREMIUM_DURATION_DAYS)

    def is_premium_active(
        self,
        user: User,
        now: datetime | None = None,
    ) -> bool:
        """Проверяет, действует ли PREMIUM (30 дней с даты оформления)."""
        if user.subscription_type != SubscriptionType.PREMIUM:
            return False

        expires_at = self.get_premium_expires_at(user)
        if expires_at is None:
            return False

        return self._now(now) < expires_at

    def activate_premium(
        self,
        user: User,
        started_at: datetime | None = None,
    ) -> User:
        """Оформляет или продлевает PREMIUM на 30 дней."""
        now = self._now(started_at)

        if self.is_premium_active(user=user, now=now):
            # Продлеваем от текущей даты окончания, а не сбрасываем срок.
            expires_at = self.get_premium_expires_at(user)
            assert expires_at is not None
            user.subscription_started_at = expires_at
        else:
            user.subscription_started_at = now

        user.subscription_type = SubscriptionType.PREMIUM
        return user

    def expire_premium_if_needed(
        self,
        user: User,
        now: datetime | None = None,
    ) -> User:
        """Сбрасывает PREMIUM на FREE, если срок 30 дней истёк."""
        if user.subscription_type != SubscriptionType.PREMIUM:
            return user

        if self.is_premium_active(user=user, now=now):
            return user

        user.subscription_type = SubscriptionType.FREE
        user.subscription_started_at = None
        return user

    def _current_month_bounds(
        self,
        now: datetime | None = None,
    ) -> tuple[datetime, datetime]:
        """Возвращает начало текущего месяца и начало следующего (UTC)."""
        current = self._now(now)

        period_start = current.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        if current.month == 12:
            period_end = period_start.replace(year=current.year + 1, month=1)
        else:
            period_end = period_start.replace(month=current.month + 1)

        return period_start, period_end

    async def get_monthly_interview_count(
        self,
        session: AsyncSession,
        user_id: int,
        now: datetime | None = None,
    ) -> int:
        """Возвращает число собеседований пользователя за текущий календарный месяц."""
        period_start, period_end = self._current_month_bounds(now=now)
        return await interview_repository.count_created_in_period(
            session=session,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
        )

    async def can_start_interview(
        self,
        session: AsyncSession,
        user: User,
        now: datetime | None = None,
    ) -> bool:
        """Проверяет, может ли пользователь начать новое собеседование."""
        self.expire_premium_if_needed(user=user, now=now)

        if self.is_premium_active(user=user, now=now):
            return True

        used = await self.get_monthly_interview_count(
            session=session,
            user_id=user.id,
            now=now,
        )
        return used < FREE_MONTHLY_INTERVIEW_LIMIT

    async def ensure_can_start_interview(
        self,
        session: AsyncSession,
        user: User,
        now: datetime | None = None,
    ) -> None:
        """Разрешает старт или поднимает ошибку при исчерпании лимита FREE."""
        if await self.can_start_interview(session=session, user=user, now=now):
            return

        raise InterviewLimitExceededError(
            'На бесплатном тарифе доступно только '
            f'{FREE_MONTHLY_INTERVIEW_LIMIT} собеседования в месяц.\n'
            f'Оформите PREMIUM на {PREMIUM_DURATION_DAYS} дней '
            'через кнопку «💎 PREMIUM», '
            'чтобы проходить собеседования без ограничений.'
        )


subscription_service = SubscriptionService()
