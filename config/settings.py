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

    @property
    def database_url(self) -> str:
        """Строка подключения к БД."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}'
            f':{self.postgres_password.get_secret_value()}'
            f'@{self.postgres_server}'
            f':{self.postgres_port}'
            f'/{self.postgres_db}'
        )

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='forbid',
    )


settings = Settings()
