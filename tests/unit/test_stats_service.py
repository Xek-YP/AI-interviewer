from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from jinja2 import Environment, FileSystemLoader

from services.stats_service import (
    DashboardStats,
    start_of_local_day,
    stats_service,
)


def _example_stats() -> DashboardStats:
    return DashboardStats(
        users_total=1248,
        users_today=37,
        interviews_total=3842,
        interviews_today=21,
        premium_total=96,
        premium_today=4,
        revenue_stars=24000,
    )


def test_dashboard_matches_sample_wording():
    """Строки на странице совпадают с примером сводки."""
    stats = _example_stats()

    assert stats.users_total_line == 'Пользователей: 1 248'
    assert stats.today_users_line == '+37 пользователей'
    assert stats.today_interviews_line == '+21 интервью'
    assert stats.today_premium_line == '+4 Premium'
    assert stats.total_users_line == '1 248 пользователей'
    assert stats.total_interviews_line == '3 842 интервью'
    assert stats.total_premium_line == '96 Premium-покупок'
    assert stats.revenue_line == '24 000 ⭐'


def test_user_word_follows_russian_plural():
    """1, 2 и 5 пользователей получают разные формы."""
    assert DashboardStats(1, 1, 0, 0, 0, 0, 0).today_users_line == (
        '+1 пользователь'
    )
    assert DashboardStats(2, 2, 0, 0, 0, 0, 0).today_users_line == (
        '+2 пользователя'
    )
    assert DashboardStats(5, 5, 0, 0, 0, 0, 0).total_users_line == (
        '5 пользователей'
    )
    assert DashboardStats(0, 0, 0, 0, 1, 0, 0).total_premium_line == (
        '1 Premium-покупка'
    )


def test_today_starts_at_moscow_midnight():
    """«Сегодня» считается с полуночи по Москве, а не по UTC."""
    late_evening_utc = datetime(2026, 9, 30, 21, 30, tzinfo=timezone.utc)

    start = start_of_local_day(late_evening_utc, 'Europe/Moscow')

    assert start == datetime(
        2026, 10, 1, 0, 0, tzinfo=start.tzinfo
    )


@pytest.mark.asyncio
async def test_collect_maps_query_results():
    """Счётчики и сумма успешных оплат попадают в сводку."""
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[1248, 37, 3842, 21, 96, 4, 24000])
    now = datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc)

    stats = await stats_service.collect(
        session,
        now=now,
        timezone_name='Europe/Moscow',
    )

    assert stats == _example_stats()
    today_users_stmt = session.scalar.await_args_list[1].args[0]
    assert start_of_local_day(now, 'Europe/Moscow') in (
        today_users_stmt.compile().params.values()
    )


def test_stats_template_renders_sample():
    """Шаблон показывает все блоки примера."""
    env = Environment(loader=FileSystemLoader('admin/templates'))
    html = env.get_template('stats.html').render(
        request=SimpleNamespace(session={'admin_authenticated': True}),
        stats=_example_stats(),
        active_page='stats',
    )

    for line in (
        'Пользователей: 1 248',
        'За сегодня',
        '+37 пользователей',
        '+21 интервью',
        '+4 Premium',
        'Всего',
        '1 248 пользователей',
        '3 842 интервью',
        '96 Premium-покупок',
        'Доход',
        '24 000 ⭐',
    ):
        assert line in html
    assert 'href="/admin/stats"' in html
    assert 'active' in html
