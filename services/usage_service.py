from datetime import datetime, timezone

from redis.asyncio import Redis

from config.settings import settings
from exceptions.llm_exception import LlmBudgetExceededError

BUDGET_MESSAGE = (
    'На сегодня лимит собеседований исчерпан. '
    'Попробуйте завтра.'
)


class UsageService:
    """Считает запросы к LLM и останавливает их после дневного предела."""

    def __init__(self) -> None:
        self._redis: Redis | None = None

    def _client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    async def reserve_llm_request(self) -> None:
        """Занимает один запрос к LLM или отклоняет его при превышении лимита."""
        limit = settings.daily_llm_request_limit
        if limit <= 0:
            return

        day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        redis = self._client()
        count_key = f'llm:requests:{day}'
        count = int(await redis.incr(count_key))
        if count == 1:
            await redis.expire(count_key, 60 * 60 * 48)

        if count <= limit:
            return

        alert_key = f'llm:budget-alert:{day}'
        alert_set = await redis.set(alert_key, '1', nx=True, ex=60 * 60 * 48)
        raise LlmBudgetExceededError(
            BUDGET_MESSAGE,
            notify_admin=bool(alert_set),
        )


usage_service = UsageService()
