from urllib.parse import quote

from pydantic.types import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    telegram_bot_token: str
    admin_telegram_id: int

    gemini_api_key: SecretStr
    deepseek_api_key: SecretStr

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_server: str
    postgres_port: int = 5432

    admin_username: str = 'admin'
    admin_password: SecretStr = SecretStr('admin')
    admin_secret_key: SecretStr = SecretStr('change-me-admin-secret')
    admin_host: str = '127.0.0.1'
    admin_port: int = 8000

    premium_price_stars: int = 100
    payment_provider_token: str = ''
    payment_currency: str = 'XTR'

    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr | None = None

    daily_llm_request_limit: int = 200

    @property
    def database_url(self) -> str:
        """Строка подключения к БД."""
        user = quote(self.postgres_user, safe='')
        password = quote(self.postgres_password.get_secret_value(), safe='')
        database = quote(self.postgres_db, safe='')
        return (
            f'postgresql+asyncpg://{user}:{password}'
            f'@{self.postgres_server}:{self.postgres_port}/{database}'
        )

    @property
    def redis_url(self) -> str:
        """Строка подключения к Redis для FSM."""
        if self.redis_password is not None:
            password = self.redis_password.get_secret_value()
            if password:
                encoded = quote(password, safe='')
                return (
                    f'redis://:{encoded}'
                    f'@{self.redis_host}:{self.redis_port}/{self.redis_db}'
                )
        return f'redis://{self.redis_host}:{self.redis_port}/{self.redis_db}'

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='forbid',
    )


settings = Settings()
