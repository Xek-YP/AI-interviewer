import asyncio
import logging
import uuid

from redis.asyncio import Redis

from config.settings import settings

LOCK_KEY = 'bot:instance'
LOCK_TTL_SECONDS = 30
REFRESH_EVERY_SECONDS = 10

_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""

logger = logging.getLogger(__name__)

_REFRESH_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('expire', KEYS[1], ARGV[2])
end
return 0
"""


class BotAlreadyRunning(Exception):
    """Другой процесс бота уже держит блокировку."""


class InstanceLock:
    """Не даёт запустить второй процесс, который читает те же апдейты Telegram."""

    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis
        self._token = str(uuid.uuid4())

    def _client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    async def acquire(self) -> None:
        """Занимает блокировку или сообщает, что бот уже запущен."""
        acquired = await self._client().set(
            LOCK_KEY,
            self._token,
            nx=True,
            ex=LOCK_TTL_SECONDS,
        )
        if not acquired:
            raise BotAlreadyRunning(
                'Бот уже запущен в другом окне. '
                'Остановите его, прежде чем открывать второе.'
            )

    async def refresh_forever(self) -> None:
        """Продлевает блокировку, пока процесс жив."""
        while True:
            await asyncio.sleep(REFRESH_EVERY_SECONDS)
            try:
                await self._client().eval(
                    _REFRESH_SCRIPT,
                    1,
                    LOCK_KEY,
                    self._token,
                    str(LOCK_TTL_SECONDS),
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception('Не удалось продлить блокировку запуска')

    async def release(self) -> None:
        """Снимает блокировку, если её держит этот процесс."""
        if self._redis is None:
            return
        await self._redis.eval(
            _RELEASE_SCRIPT,
            1,
            LOCK_KEY,
            self._token,
        )
        await self._redis.aclose()
        self._redis = None
