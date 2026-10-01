from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from database.models.interview import Interview
from database.models.payment import Payment, PaymentStatus
from database.models.user import User


def format_count(value: int) -> str:
    """Группирует тысячи пробелом: 1248 → 1 248."""
    return f'{value:,}'.replace(',', ' ')


def ru_plural(count: int, one: str, few: str, many: str) -> str:
    """Выбирает форму слова для целого числа."""
    number = abs(count)
    last_two = number % 100
    last = number % 10
    if 11 <= last_two <= 14:
        return many
    if last == 1:
        return one
    if 2 <= last <= 4:
        return few
    return many


def start_of_local_day(moment: datetime, timezone_name: str) -> datetime:
    """Возвращает локальную полночь для момента времени."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(ZoneInfo(timezone_name))
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


@dataclass(frozen=True)
class DashboardStats:
    """Сводка по пользователям, интервью и оплатам."""

    users_total: int
    users_today: int
    interviews_total: int
    interviews_today: int
    premium_total: int
    premium_today: int
    revenue_stars: int

    @property
    def users_total_line(self) -> str:
        return f'Пользователей: {format_count(self.users_total)}'

    @property
    def today_users_line(self) -> str:
        word = ru_plural(
            self.users_today,
            'пользователь',
            'пользователя',
            'пользователей',
        )
        return f'+{format_count(self.users_today)} {word}'

    @property
    def today_interviews_line(self) -> str:
        return f'+{format_count(self.interviews_today)} интервью'

    @property
    def today_premium_line(self) -> str:
        return f'+{format_count(self.premium_today)} Premium'

    @property
    def total_users_line(self) -> str:
        word = ru_plural(
            self.users_total,
            'пользователь',
            'пользователя',
            'пользователей',
        )
        return f'{format_count(self.users_total)} {word}'

    @property
    def total_interviews_line(self) -> str:
        return f'{format_count(self.interviews_total)} интервью'

    @property
    def total_premium_line(self) -> str:
        word = ru_plural(
            self.premium_total,
            'Premium-покупка',
            'Premium-покупки',
            'Premium-покупок',
        )
        return f'{format_count(self.premium_total)} {word}'

    @property
    def revenue_line(self) -> str:
        return f'{format_count(self.revenue_stars)} ⭐'


class StatsService:
    """Считает показатели для страницы статистики."""

    async def collect(
        self,
        session: AsyncSession,
        now: datetime | None = None,
        timezone_name: str | None = None,
    ) -> DashboardStats:
        """Собирает показатели за сегодня и за всё время."""
        moment = now or datetime.now(timezone.utc)
        zone_name = timezone_name or settings.stats_timezone
        day_start = start_of_local_day(moment, zone_name)
        successful = Payment.status == PaymentStatus.SUCCESS

        users_total = await self._count(session, User)
        users_today = await self._count(
            session,
            User,
            User.created_at >= day_start,
        )
        interviews_total = await self._count(session, Interview)
        interviews_today = await self._count(
            session,
            Interview,
            Interview.created_at >= day_start,
        )
        premium_total = await self._count(session, Payment, successful)
        premium_today = await self._count(
            session,
            Payment,
            successful,
            Payment.created_at >= day_start,
        )
        revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.total_amount), 0)).where(
                successful
            )
        )
        return DashboardStats(
            users_total=users_total,
            users_today=users_today,
            interviews_total=interviews_total,
            interviews_today=interviews_today,
            premium_total=premium_total,
            premium_today=premium_today,
            revenue_stars=int(revenue or 0),
        )

    async def _count(
        self,
        session: AsyncSession,
        model: type,
        *criteria,
    ) -> int:
        stmt = select(func.count()).select_from(model)
        if criteria:
            stmt = stmt.where(*criteria)
        value = await session.scalar(stmt)
        return int(value or 0)


stats_service = StatsService()
