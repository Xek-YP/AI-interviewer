from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants.subscription import PREMIUM_DURATION_DAYS, PREMIUM_PRODUCT_PAYLOAD
from database.enums import SubscriptionType
from services.payment_service import PaymentService
from services.subscription_service import SubscriptionService


@pytest.fixture
def payment_service():
    return PaymentService()


@pytest.fixture
def subscription_service_obj():
    return SubscriptionService()


def test_build_and_parse_payload(payment_service):
    """Payload инвойса содержит id пользователя и корректно парсится."""
    payload = payment_service.build_payload(42)
    assert payload == f'{PREMIUM_PRODUCT_PAYLOAD}:42'
    assert payment_service.parse_user_id(payload) == 42


def test_parse_invalid_payload(payment_service):
    """Некорректный payload возвращает None."""
    assert payment_service.parse_user_id('other:1') is None
    assert payment_service.parse_user_id(f'{PREMIUM_PRODUCT_PAYLOAD}:abc') is None


def test_activate_premium_extends_active_subscription(
    subscription_service_obj, premium_user
):
    """Повторная покупка продлевает PREMIUM, а не сбрасывает срок."""
    started = datetime(2026, 9, 15, tzinfo=timezone.utc)
    premium_user.subscription_started_at = started
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)

    subscription_service_obj.activate_premium(premium_user, started_at=now)

    assert premium_user.subscription_type == SubscriptionType.PREMIUM
    assert premium_user.subscription_started_at == started + timedelta(
        days=PREMIUM_DURATION_DAYS
    )


@pytest.mark.asyncio
async def test_complete_premium_payment_activates_user(
    payment_service, session, user
):
    """Успешная оплата сохраняет платёж и активирует PREMIUM."""
    payment = MagicMock()
    with (
        patch(
            'services.payment_service.payment_repository.get_by_telegram_charge_id',
            AsyncMock(return_value=None),
        ),
        patch(
            'services.payment_service.payment_repository.create',
            AsyncMock(return_value=payment),
        ),
        patch(
            'services.payment_service.payment_repository.mark_success',
            AsyncMock(return_value=payment),
        ),
    ):
        result = await payment_service.complete_premium_payment(
            session=session,
            user=user,
            telegram_payment_charge_id='tg_charge_1',
            provider_payment_charge_id='provider_1',
            currency='XTR',
            total_amount=100,
            payload=payment_service.build_payload(user.id),
        )

    assert result.subscription_type == SubscriptionType.PREMIUM
    assert result.subscription_started_at is not None
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_complete_premium_payment_is_idempotent(
    payment_service, session, user
):
    """Повторная обработка того же charge id не создаёт новый платёж."""
    with (
        patch(
            'services.payment_service.payment_repository.get_by_telegram_charge_id',
            AsyncMock(return_value=MagicMock()),
        ),
        patch(
            'services.payment_service.payment_repository.create',
            AsyncMock(),
        ) as create,
    ):
        await payment_service.complete_premium_payment(
            session=session,
            user=user,
            telegram_payment_charge_id='tg_charge_1',
            provider_payment_charge_id=None,
            currency='XTR',
            total_amount=100,
            payload=payment_service.build_payload(user.id),
        )

    create.assert_not_awaited()
