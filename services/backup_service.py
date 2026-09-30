import asyncio
import logging
from datetime import datetime
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)

POSTGRES_CONTAINER = 'my_postgres'
BACKUP_DIR = Path('backups')
BACKUP_KEEP = 7
BACKUP_INTERVAL_SECONDS = 24 * 60 * 60
BACKUP_RETRY_SECONDS = 15 * 60


def prune_old_backups(directory: Path, keep: int = BACKUP_KEEP) -> None:
    """Оставляет только последние копии базы."""
    files = sorted(
        directory.glob('ai-interviewer-*.dump'),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old in files[keep:]:
        old.unlink()


async def create_backup() -> Path:
    """Снимает копию Postgres из локального контейнера."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    process = await asyncio.create_subprocess_exec(
        'docker',
        'exec',
        POSTGRES_CONTAINER,
        'pg_dump',
        '-U',
        settings.postgres_user,
        '-d',
        settings.postgres_db,
        '-F',
        'c',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        details = stderr.decode('utf-8', errors='replace').strip()
        raise RuntimeError(details or 'pg_dump завершился с ошибкой')

    filename = datetime.now().strftime('ai-interviewer-%Y%m%d-%H%M%S.dump')
    target = BACKUP_DIR / filename
    target.write_bytes(stdout)
    prune_old_backups(BACKUP_DIR)
    return target


async def backup_loop() -> None:
    """Периодически сохраняет копию базы, не останавливая бота при ошибке."""
    while True:
        try:
            path = await create_backup()
            logger.info('Копия базы сохранена: %s', path)
            await asyncio.sleep(BACKUP_INTERVAL_SECONDS)
        except Exception:
            logger.exception('Не удалось сделать копию базы')
            await asyncio.sleep(BACKUP_RETRY_SECONDS)
