import logging


def setup_logging() -> None:
    """Настраивает logging приложения."""

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                'logs/app.log',
                encoding='UTF-8',
            ),
        ],
    )