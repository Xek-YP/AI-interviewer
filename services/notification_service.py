from aiogram import Bot

from config.settings import settings


class NotificationService:

    async def send_error(
        self,
        bot: Bot,
        exception: Exception,
        user_id: int | None = None,
    ):
        message = (
            "🚨 Ошибка в боте\n\n"
            f"Тип: {type(exception).__name__}\n"
            f"Ошибка: {exception}\n"
        )

        if user_id:
            message += (
                f"\nПользователь: {user_id}"
            )

        await bot.send_message(
            chat_id=settings.admin_telegram_id,
            text=message[:4000],
        )


notification_service = NotificationService()
