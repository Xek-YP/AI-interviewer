import os
from datetime import datetime, timezone

import pytest
from pydantic.types import SecretStr

from config.settings import Settings, settings
from exceptions.llm_exception import LlmBudgetExceededError
from services.backup_service import prune_old_backups
from services.instance_lock import BotAlreadyRunning, InstanceLock
from services.local_config import ensure_safe_local_config
from services.usage_service import usage_service


def _settings(**overrides) -> Settings:
    values = {
        'telegram_bot_token': 'test-token',
        'admin_telegram_id': 1,
        'gemini_api_key': SecretStr('gemini'),
        'deepseek_api_key': SecretStr('deepseek'),
        'postgres_user': 'bot_user',
        'postgres_password': SecretStr('db-password'),
        'postgres_db': 'db',
        'postgres_server': 'localhost',
        'admin_password': SecretStr('strong-local-password'),
        'admin_secret_key': SecretStr('not-the-default-secret'),
        'admin_host': '127.0.0.1',
        'redis_password': SecretStr('redis-secret'),
    }
    values.update(overrides)
    return Settings(**values)


def test_local_config_accepts_loopback_with_own_secrets():
    """Домашний запуск на localhost с своими паролями разрешён."""
    ensure_safe_local_config(_settings())


def test_local_config_rejects_public_admin_host():
    """Админка не должна слушать все сетевые интерфейсы."""
    with pytest.raises(RuntimeError, match='ADMIN_HOST'):
        ensure_safe_local_config(_settings(admin_host='0.0.0.0'))


def test_local_config_rejects_default_admin_password():
    """Пароль admin из примера нельзя использовать при запуске."""
    with pytest.raises(RuntimeError, match='ADMIN_PASSWORD'):
        ensure_safe_local_config(
            _settings(admin_password=SecretStr('admin')),
        )


def test_local_config_requires_redis_password():
    """Redis без пароля для домашнего запуска не подходит."""
    with pytest.raises(RuntimeError, match='REDIS_PASSWORD'):
        ensure_safe_local_config(_settings(redis_password=SecretStr('')))


def test_prune_old_backups_keeps_newest(tmp_path):
    """Из копий базы остаются только последние семь."""
    base = 1_700_000_000
    for index in range(8):
        path = tmp_path / f'ai-interviewer-{index}.dump'
        path.write_bytes(b'backup')
        moment = base + index
        os.utime(path, (moment, moment))

    prune_old_backups(tmp_path, keep=7)

    names = {path.name for path in tmp_path.glob('ai-interviewer-*.dump')}
    assert 'ai-interviewer-0.dump' not in names
    assert len(names) == 7


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return None
        self.values[key] = value
        return True

    async def incr(self, key):
        current = int(self.values.get(key, '0')) + 1
        self.values[key] = str(current)
        return current

    async def expire(self, key, ttl):
        return True

    async def eval(self, script, numkeys, key, token, *args):
        if self.values.get(key) != token:
            return 0
        if "del" in script:
            del self.values[key]
        return 1

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_second_process_cannot_take_the_lock():
    """Второй запуск не забирает апдейты у уже работающего бота."""
    redis = _FakeRedis()
    first = InstanceLock(redis=redis)
    second = InstanceLock(redis=redis)

    await first.acquire()
    with pytest.raises(BotAlreadyRunning):
        await second.acquire()

    await first.release()
    await second.acquire()


@pytest.mark.asyncio
async def test_llm_budget_notifies_admin_once(monkeypatch):
    """После дневного предела пользователь получает отказ, админ — одно сообщение."""
    monkeypatch.setattr(settings, 'daily_llm_request_limit', 1)
    fake = _FakeRedis()
    usage_service._redis = fake

    await usage_service.reserve_llm_request()
    with pytest.raises(LlmBudgetExceededError) as first:
        await usage_service.reserve_llm_request()
    with pytest.raises(LlmBudgetExceededError) as second:
        await usage_service.reserve_llm_request()

    assert first.value.notify_admin is True
    assert second.value.notify_admin is False
    assert datetime.now(timezone.utc).strftime('%Y-%m-%d') in next(
        key for key in fake.values if key.startswith('llm:requests:')
    )
    usage_service._redis = None
