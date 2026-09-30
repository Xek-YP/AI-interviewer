import asyncio
import logging
import time

from admin.app import start_admin_server
from bot.app import start_bot
from config.logging_config import setup_logging
from services.backup_service import backup_loop
from services.instance_lock import LOCK_TTL_SECONDS, BotAlreadyRunning, InstanceLock
from services.local_config import ensure_safe_local_config

logger = logging.getLogger(__name__)
RESTART_DELAY_SECONDS = 5


async def run() -> None:
    """Держит один экземпляр бота, админку и ежедневную копию базы."""
    lock = InstanceLock()
    await lock.acquire()
    refresh_task = asyncio.create_task(lock.refresh_forever())
    try:
        await asyncio.gather(
            start_bot(),
            start_admin_server(),
            backup_loop(),
        )
    finally:
        refresh_task.cancel()
        try:
            await refresh_task
        except asyncio.CancelledError:
            pass
        try:
            await lock.release()
        except Exception:
            logger.exception('Не удалось снять блокировку запуска')
            await asyncio.sleep(LOCK_TTL_SECONDS)


def main() -> None:
    setup_logging()
    try:
        ensure_safe_local_config()
    except RuntimeError as exc:
        logger.error('%s', exc)
        return

    while True:
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            logger.info('Остановка бота')
            return
        except BotAlreadyRunning as exc:
            logger.error('%s', exc)
            return
        except Exception:
            logger.exception(
                'Процесс упал. Перезапуск через %s секунд.',
                RESTART_DELAY_SECONDS,
            )
            time.sleep(RESTART_DELAY_SECONDS)


if __name__ == '__main__':
    main()
