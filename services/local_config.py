from config.settings import Settings, settings

LOOPBACK_HOSTS = {'127.0.0.1', 'localhost', '::1'}
DEFAULT_ADMIN_PASSWORDS = {'', 'admin'}
DEFAULT_ADMIN_SECRETS = {'', 'change-me-admin-secret'}


def ensure_safe_local_config(config: Settings = settings) -> None:
    """Проверяет, что бот на этом компьютере не открыт с паролями по умолчанию."""
    if config.admin_host not in LOOPBACK_HOSTS:
        raise RuntimeError(
            'Админка должна быть доступна только на этом компьютере. '
            'Поставьте ADMIN_HOST=127.0.0.1'
        )

    password = config.admin_password.get_secret_value()
    secret = config.admin_secret_key.get_secret_value()
    if (
        password in DEFAULT_ADMIN_PASSWORDS
        or secret in DEFAULT_ADMIN_SECRETS
    ):
        raise RuntimeError(
            'Смените ADMIN_PASSWORD и ADMIN_SECRET_KEY в .env. '
            'Значения по умолчанию для запуска не подходят.'
        )

    redis_password = ''
    if config.redis_password is not None:
        redis_password = config.redis_password.get_secret_value()
    if not redis_password:
        raise RuntimeError(
            'Задайте REDIS_PASSWORD в .env. '
            'Redis запускается только с паролем и только на этом компьютере.'
        )
