import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    """Настраивает logging приложения."""
    log_dir = Path('logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s | '
            '%(levelname)s | '
            '%(name)s | '
            '%(message)s'
        ),
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                log_dir / 'app.log',
                maxBytes=2_000_000,
                backupCount=5,
                encoding='utf-8',
            ),
        ],
    )
