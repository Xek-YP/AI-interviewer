import asyncio

from admin.app import start_admin_server
from bot.app import start_bot


async def run() -> None:
    """Запускает Telegram-бота и веб-админку параллельно."""
    await asyncio.gather(
        start_bot(),
        start_admin_server(),
    )


def main() -> None:
    asyncio.run(run())


if __name__ == '__main__':
    main()
