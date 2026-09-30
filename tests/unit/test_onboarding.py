from bot.handlers.messages import (
    build_free_tariff_block,
    build_onboarding_message,
    build_premium_tariff_block,
    format_interview_count,
)
from services.payment_service import PaymentService


def test_format_interview_count_russian_plural():
    """Число собеседований склоняется по правилам русского языка."""
    assert format_interview_count(1) == '1 собеседование'
    assert format_interview_count(2) == '2 собеседования'
    assert format_interview_count(5) == '5 собеседований'
    assert format_interview_count(11) == '11 собеседований'
    assert format_interview_count(21) == '21 собеседование'


def test_onboarding_message_shows_product_and_premium_price():
    """Первый экран объясняет продукт и цену Premium до запуска."""
    text = build_onboarding_message(
        build_free_tariff_block(price_label='250 Stars', free_limit=2),
    )

    assert '🤖 AI-Собеседование' in text
    assert 'Python / Backend' in text
    assert 'Junior / Middle / Senior' in text
    assert 'Персональные вопросы по вакансии' in text
    assert 'Оценка каждого ответа' in text
    assert 'Итоговый балл и разбор ошибок' in text
    assert '🎁 Бесплатно: 2 собеседования в месяц' in text
    assert '💎 Premium: безлимит — 250 Stars / месяц' in text
    assert 'Привет' not in text


def test_premium_tariff_block_hides_sales_offer():
    """Активный Premium не продаётся повторно на первом экране."""
    text = build_premium_tariff_block('12.10.2026')
    assert text == '💎 Premium активен до 12.10.2026 — безлимит'


def test_monthly_price_uses_stars_label(monkeypatch):
    """Для Telegram Stars цена на первом экране читается как «N Stars»."""
    monkeypatch.setattr(
        'services.payment_service.settings.premium_price_stars',
        250,
    )
    monkeypatch.setattr(
        'services.payment_service.settings.payment_currency',
        'XTR',
    )

    assert PaymentService().format_monthly_price_text() == '250 Stars'
