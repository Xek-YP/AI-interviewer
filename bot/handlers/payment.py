import logging

from aiogram import F, Bot, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    CallbackQuery,
    Message,
    PreCheckoutQuery,
)

from bot.keyboards.buttons_text import BUY_PREMIUM, BUY_PREMIUM_CALLBACK
from config.settings import settings
from constants.subscription import (
    PREMIUM_DESCRIPTION,
    PREMIUM_DURATION_DAYS,
    PREMIUM_TITLE,
)
from database.session import AsyncSessionLocal
from services.payment_service import payment_service
from services.subscription_service import subscription_service
from services.user_service import user_service


router = Router()
logger = logging.getLogger(__name__)


async def send_premium_invoice(bot: Bot, chat_id: int, user_id: int) -> None:
    """Отправляет пользователю счёт на оплату PREMIUM."""
    if settings.premium_price_stars <= 0:
        raise ValueError(
            'Цена PREMIUM не задана. Укажите PREMIUM_PRICE_STARS в .env.'
        )

    await bot.send_invoice(
        chat_id=chat_id,
        title=PREMIUM_TITLE,
        description=PREMIUM_DESCRIPTION,
        payload=payment_service.build_payload(user_id),
        provider_token=payment_service.get_provider_token(),
        currency=settings.payment_currency.upper(),
        prices=payment_service.get_invoice_prices(),
    )


async def _reject_if_premium_active(message_or_callback_message, user) -> bool:
    """True, если активный PREMIUM — повторная покупка запрещена."""
    if not subscription_service.is_premium_active(user):
        return False

    expires_at = subscription_service.get_premium_expires_at(user)
    expires_text = (
        expires_at.strftime('%d.%m.%Y')
        if expires_at
        else 'конца текущего срока'
    )
    await message_or_callback_message.answer(
        'У вас уже активен PREMIUM '
        f'до {expires_text}.\n'
        'Повторная покупка недоступна, пока действует текущая подписка.\n'
        'Новую можно оформить после окончания срока.'
    )
    return True


@router.message(F.text == BUY_PREMIUM)
async def buy_premium_handler(message: Message, bot: Bot):
    """Показывает оферту и отправляет счёт, если PREMIUM ещё нет."""
    if message.from_user is None:
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.get_user(
            session=session,
            telegram_id=message.from_user.id,
        )
        await subscription_service.sync_subscription_status(
            session=session,
            user=user,
        )
        if await _reject_if_premium_active(message, user):
            return
        user_id = user.id

    price = payment_service.format_price_text()
    await message.answer(
        '💎 PREMIUM подписка\n\n'
        f'• безлимитные собеседования на {PREMIUM_DURATION_DAYS} дней\n'
        f'• цена: {price}\n\n'
        'Сейчас открою счёт на оплату в Telegram.'
    )

    try:
        async with AsyncSessionLocal() as session:
            user = await user_service.get_user(
                session=session,
                telegram_id=message.from_user.id,
            )
            if subscription_service.is_premium_active(user):
                await _reject_if_premium_active(message, user)
                return
            await payment_service.create_pending_payment(
                session=session,
                user=user,
            )
        await send_premium_invoice(bot, message.chat.id, user_id)
    except (TelegramAPIError, ValueError) as e:
        logger.exception('Не удалось отправить invoice PREMIUM')
        await message.answer(
            'Не удалось открыть оплату.\n'
            f'Причина: {e}\n\n'
            'Проверьте настройки оплаты в .env.'
        )


@router.callback_query(F.data == BUY_PREMIUM_CALLBACK)
async def buy_premium_callback(callback: CallbackQuery, bot: Bot):
    """Создаёт инвойс после нажатия inline-кнопки."""
    if callback.from_user is None:
        await callback.answer()
        return

    await callback.answer()
    target = callback.message
    chat_id = (
        callback.message.chat.id
        if callback.message
        else callback.from_user.id
    )

    try:
        async with AsyncSessionLocal() as session:
            user = await user_service.get_user(
                session=session,
                telegram_id=callback.from_user.id,
            )
            await subscription_service.sync_subscription_status(
                session=session,
                user=user,
            )
            if target and await _reject_if_premium_active(target, user):
                return
            if subscription_service.is_premium_active(user):
                return

            await payment_service.create_pending_payment(
                session=session,
                user=user,
            )
            user_id = user.id

        await send_premium_invoice(bot, chat_id, user_id)
    except (TelegramAPIError, ValueError) as e:
        logger.exception('Не удалось отправить invoice PREMIUM из callback')
        text = f'Не удалось открыть оплату.\nПричина: {e}'
        if callback.message:
            await callback.message.answer(text)
        else:
            await bot.send_message(callback.from_user.id, text)


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Подтверждает pre-checkout только если PREMIUM ещё не активен."""
    user_id = payment_service.parse_user_id(pre_checkout_query.invoice_payload)
    if user_id is None:
        await pre_checkout_query.answer(
            ok=False,
            error_message='Некорректный платёж. Попробуйте ещё раз.',
        )
        return

    async with AsyncSessionLocal() as session:
        from database.repositories.user_repository import user_repository

        user = await user_repository.get_by_id(session=session, user_id=user_id)
        if user is None:
            await pre_checkout_query.answer(
                ok=False,
                error_message='Пользователь не найден.',
            )
            return

        await subscription_service.sync_subscription_status(
            session=session,
            user=user,
        )
        if subscription_service.is_premium_active(user):
            await pre_checkout_query.answer(
                ok=False,
                error_message=(
                    'PREMIUM уже активен. '
                    'Дождитесь окончания текущей подписки.'
                ),
            )
            return

    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Активирует PREMIUM после успешной оплаты."""
    if message.from_user is None or message.successful_payment is None:
        return

    payment = message.successful_payment
    payload_user_id = payment_service.parse_user_id(payment.invoice_payload)
    if payload_user_id is None:
        await message.answer(
            'Оплата получена, но данные платежа некорректны. '
            'Напишите в поддержку.'
        )
        return

    async with AsyncSessionLocal() as session:
        user = await user_service.get_user(
            session=session,
            telegram_id=message.from_user.id,
        )
        if user.id != payload_user_id:
            await message.answer(
                'Оплата не совпала с вашим аккаунтом. '
                'Напишите в поддержку.'
            )
            return

        await subscription_service.sync_subscription_status(
            session=session,
            user=user,
        )
        if subscription_service.is_premium_active(user):
            await message.answer(
                'Оплата получена, но PREMIUM у вас уже был активен.\n'
                'Подписка не продлевалась повторно. '
                'Обратитесь в поддержку, если списание прошло ошибочно.'
            )
            return

        await payment_service.complete_premium_payment(
            session=session,
            user=user,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            provider_payment_charge_id=payment.provider_payment_charge_id,
            currency=payment.currency,
            total_amount=payment.total_amount,
            payload=payment.invoice_payload,
        )
        expires_at = subscription_service.get_premium_expires_at(user)

    expires_text = (
        expires_at.strftime('%d.%m.%Y')
        if expires_at
        else f'{PREMIUM_DURATION_DAYS} дней'
    )
    await message.answer(
        '✅ Оплата прошла успешно!\n\n'
        f'PREMIUM активен до {expires_text}.\n'
        'Теперь можно проходить собеседования без лимита FREE.'
    )
