from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from constants.subscription import (
    FREE_MONTHLY_INTERVIEW_LIMIT,
    PREMIUM_DURATION_DAYS,
)
from database.enums import SubscriptionType
from exceptions import InterviewLimitExceededError
from services.subscription_service import SubscriptionService


@pytest.fixture
def service():
    return SubscriptionService()


def test_current_month_bounds(service):
    """Границы месяца для FREE-лимита — календарный месяц UTC."""
    now = datetime(2026, 9, 15, 12, 30, tzinfo=timezone.utc)

    period_start, period_end = service._current_month_bounds(now=now)

    assert period_start == datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert period_end == datetime(2026, 10, 1, tzinfo=timezone.utc)


def test_current_month_bounds_december(service):
    """Для декабря конец периода — 1 января следующего года."""
    now = datetime(2026, 12, 20, tzinfo=timezone.utc)

    period_start, period_end = service._current_month_bounds(now=now)

    assert period_start == datetime(2026, 12, 1, tzinfo=timezone.utc)
    assert period_end == datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_activate_premium_sets_30_day_period(service, user):
    """Оформление PREMIUM сохраняет дату старта для срока 30 дней."""
    started_at = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)

    service.activate_premium(user, started_at=started_at)

    assert user.subscription_type == SubscriptionType.PREMIUM
    assert user.subscription_started_at == started_at
    assert service.get_premium_expires_at(user) == started_at + timedelta(
        days=PREMIUM_DURATION_DAYS
    )


def test_is_premium_active_within_30_days(service, premium_user):
    """PREMIUM активен в течение 30 дней после оформления."""
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    premium_user.subscription_started_at = datetime(
        2026, 9, 15, tzinfo=timezone.utc
    )

    assert service.is_premium_active(premium_user, now=now) is True


def test_is_premium_active_expired_after_30_days(service, premium_user):
    """PREMIUM неактивен после 30 дней с даты оформления."""
    started_at = datetime(2026, 9, 15, tzinfo=timezone.utc)
    premium_user.subscription_started_at = started_at
    now = started_at + timedelta(days=PREMIUM_DURATION_DAYS)

    assert service.is_premium_active(premium_user, now=now) is False


def test_expire_premium_if_needed_resets_to_free(service, premium_user):
    """Истёкший PREMIUM сбрасывается на FREE."""
    started_at = datetime(2026, 9, 15, tzinfo=timezone.utc)
    premium_user.subscription_started_at = started_at
    now = started_at + timedelta(days=PREMIUM_DURATION_DAYS + 1)

    service.expire_premium_if_needed(premium_user, now=now)

    assert premium_user.subscription_type == SubscriptionType.FREE
    assert premium_user.subscription_started_at is None


@pytest.mark.asyncio
async def test_can_start_interview_active_premium_allowed(
    service, session, premium_user
):
    """Активный PREMIUM позволяет начинать собеседования без лимита."""
    premium_user.subscription_started_at = datetime(
        2026, 9, 15, tzinfo=timezone.utc
    )
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)

    with patch(
        "services.subscription_service.interview_repository.count_created_in_period",
        AsyncMock(return_value=100),
    ) as count:
        allowed = await service.can_start_interview(
            session, premium_user, now=now
        )

    assert allowed is True
    count.assert_not_awaited()


@pytest.mark.asyncio
async def test_can_start_interview_expired_premium_uses_free_limit(
    service, session, premium_user
):
    """После истечения PREMIUM применяется FREE-лимит."""
    started_at = datetime(2026, 9, 15, tzinfo=timezone.utc)
    premium_user.subscription_started_at = started_at
    now = started_at + timedelta(days=PREMIUM_DURATION_DAYS + 1)

    with patch(
        "services.subscription_service.interview_repository.count_created_in_period",
        AsyncMock(return_value=FREE_MONTHLY_INTERVIEW_LIMIT),
    ):
        allowed = await service.can_start_interview(
            session, premium_user, now=now
        )

    assert allowed is False
    assert premium_user.subscription_type == SubscriptionType.FREE


@pytest.mark.asyncio
async def test_can_start_interview_free_under_limit(service, session, user):
    """FREE-пользователь может начать собеседование, пока лимит не исчерпан."""
    with patch(
        "services.subscription_service.interview_repository.count_created_in_period",
        AsyncMock(return_value=FREE_MONTHLY_INTERVIEW_LIMIT - 1),
    ):
        allowed = await service.can_start_interview(session, user)

    assert allowed is True


@pytest.mark.asyncio
async def test_can_start_interview_free_at_limit(service, session, user):
    """FREE-пользователь не может начать собеседование после 2 интервью в месяц."""
    with patch(
        "services.subscription_service.interview_repository.count_created_in_period",
        AsyncMock(return_value=FREE_MONTHLY_INTERVIEW_LIMIT),
    ):
        allowed = await service.can_start_interview(session, user)

    assert allowed is False


@pytest.mark.asyncio
async def test_ensure_can_start_interview_raises_for_free_limit(
    service, session, user
):
    """ensure_can_start_interview поднимает ошибку при исчерпании FREE-лимита."""
    with patch.object(
        service, "can_start_interview", AsyncMock(return_value=False)
    ):
        with pytest.raises(InterviewLimitExceededError, match="бесплатном тарифе"):
            await service.ensure_can_start_interview(session, user)


@pytest.mark.asyncio
async def test_ensure_can_start_interview_passes_when_allowed(
    service, session, user
):
    """ensure_can_start_interview ничего не делает, если старт разрешён."""
    with patch.object(
        service, "can_start_interview", AsyncMock(return_value=True)
    ):
        await service.ensure_can_start_interview(session, user)


@pytest.mark.asyncio
async def test_get_monthly_interview_count(service, session, user):
    """Счётчик за месяц делегирует запрос в репозиторий с границами месяца."""
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)

    with patch(
        "services.subscription_service.interview_repository.count_created_in_period",
        AsyncMock(return_value=2),
    ) as count:
        result = await service.get_monthly_interview_count(
            session=session,
            user_id=user.id,
            now=now,
        )

    assert result == 2
    count.assert_awaited_once_with(
        session=session,
        user_id=user.id,
        period_start=datetime(2026, 9, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
