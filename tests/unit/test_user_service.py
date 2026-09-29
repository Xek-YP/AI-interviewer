from unittest.mock import AsyncMock, patch

import pytest

from services.user_service import UserService


@pytest.fixture
def service():
    return UserService()


@pytest.mark.asyncio
async def test_register_new_user(service, session, user):
    """Новый пользователь создаётся и сохраняется в БД."""
    with (
        patch(
            "services.user_service.user_repository.get_by_telegram_id",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.user_service.user_repository.create",
            AsyncMock(return_value=user),
        ) as create,
    ):
        result = await service.register_user(
            session,
            telegram_id=12345,
            first_name="Ivan",
            username="ivan",
        )

    assert result is user
    create.assert_awaited_once()
    session.flush.assert_awaited()
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_register_existing_user_updates_fields(service, session, user):
    """Повторная регистрация обновляет профиль и время активности."""
    with patch(
        "services.user_service.user_repository.get_by_telegram_id",
        AsyncMock(return_value=user),
    ):
        result = await service.register_user(
            session,
            telegram_id=12345,
            first_name="Petr",
            username="petr",
        )

    assert result is user
    assert user.first_name == "Petr"
    assert user.username == "petr"
    assert user.last_activity_at is not None
    session.commit.assert_awaited()
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_user_success(service, session, user):
    """Пользователь находится по telegram_id."""
    with patch(
        "services.user_service.user_repository.get_by_telegram_id",
        AsyncMock(return_value=user),
    ):
        result = await service.get_user(session, telegram_id=12345)

    assert result is user


@pytest.mark.asyncio
async def test_get_user_not_found(service, session):
    """Запрос несуществующего пользователя вызывает ValueError."""
    with patch(
        "services.user_service.user_repository.get_by_telegram_id",
        AsyncMock(return_value=None),
    ):
        with pytest.raises(ValueError, match="telegram_id"):
            await service.get_user(session, telegram_id=999)


@pytest.mark.asyncio
async def test_get_user_blocked(service, session, user):
    """Заблокированный пользователь не может пользоваться ботом."""
    from exceptions import UserBlockedError

    user.is_blocked = True
    with patch(
        "services.user_service.user_repository.get_by_telegram_id",
        AsyncMock(return_value=user),
    ):
        with pytest.raises(UserBlockedError, match="заблокирован"):
            await service.get_user(session, telegram_id=12345)


@pytest.mark.asyncio
async def test_register_blocked_user(service, session, user):
    """Повторный /start для заблокированного пользователя запрещён."""
    from exceptions import UserBlockedError

    user.is_blocked = True
    with patch(
        "services.user_service.user_repository.get_by_telegram_id",
        AsyncMock(return_value=user),
    ):
        with pytest.raises(UserBlockedError, match="заблокирован"):
            await service.register_user(
                session,
                telegram_id=12345,
                first_name="Ivan",
            )
