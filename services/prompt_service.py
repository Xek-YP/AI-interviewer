from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants.prompts import DEFAULT_PROMPTS
from database.models import Prompt
from database.session import AsyncSessionLocal


class PromptService:
    """Сервис хранения и чтения промптов LLM."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def invalidate_cache(self) -> None:
        """Сбрасывает кэш промптов."""
        self._cache.clear()

    async def ensure_defaults(self, session: AsyncSession) -> None:
        """Создаёт промпты по умолчанию, если их ещё нет в БД."""
        for key, data in DEFAULT_PROMPTS.items():
            existing = await session.get(Prompt, key)
            if existing is None:
                session.add(
                    Prompt(
                        key=key,
                        title=data['title'],
                        content=data['content'],
                    )
                )
        await session.commit()
        self.invalidate_cache()

    async def list_prompts(self, session: AsyncSession) -> list[Prompt]:
        """Возвращает все промпты."""
        result = await session.execute(
            select(Prompt).order_by(Prompt.title.asc())
        )
        return list(result.scalars().all())

    async def get_prompt(
        self,
        session: AsyncSession,
        key: str,
    ) -> Prompt | None:
        """Возвращает промпт по ключу."""
        return await session.get(Prompt, key)

    async def get_content(self, key: str) -> str:
        """Возвращает текст промпта с fallback на константы."""
        if key in self._cache:
            return self._cache[key]

        try:
            async with AsyncSessionLocal() as session:
                prompt = await session.get(Prompt, key)
                if prompt is not None:
                    self._cache[key] = prompt.content
                    return prompt.content
        except Exception:
            pass

        fallback = DEFAULT_PROMPTS[key]['content']
        self._cache[key] = fallback
        return fallback

    async def update_prompt(
        self,
        session: AsyncSession,
        key: str,
        content: str,
    ) -> Prompt:
        """Обновляет текст промпта."""
        prompt = await session.get(Prompt, key)
        if prompt is None:
            raise ValueError(f'Промпт "{key}" не найден.')

        prompt.content = content
        prompt.updated_at = datetime.now(timezone.utc)
        await session.commit()
        self._cache[key] = content
        return prompt


prompt_service = PromptService()
