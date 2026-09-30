from urllib.parse import unquote, urlparse

from pydantic.types import SecretStr

from config.settings import Settings


def _settings(**overrides) -> Settings:
    values = {
        'telegram_bot_token': 'test-token',
        'admin_telegram_id': 1,
        'gemini_api_key': SecretStr('gemini'),
        'deepseek_api_key': SecretStr('deepseek'),
        'postgres_user': 'bot_user',
        'postgres_password': SecretStr('xek-admin?secret'),
        'postgres_db': 'ai_interviewer',
        'postgres_server': 'localhost',
        'redis_password': SecretStr('Xek-admin?secret'),
    }
    values.update(overrides)
    return Settings(**values)


def test_redis_url_encodes_question_mark_in_password():
    """Символ ? в пароле Redis не должен становиться началом query."""
    parsed = urlparse(_settings().redis_url)

    assert parsed.port == 6379
    assert parsed.query == ''
    assert unquote(parsed.password) == 'Xek-admin?secret'
    assert parsed.hostname == 'localhost'


def test_database_url_encodes_question_mark_in_password():
    """Символ ? в пароле Postgres не должен ломать разбор URL."""
    parsed = urlparse(_settings().database_url)

    assert parsed.port == 5432
    assert parsed.query == ''
    assert unquote(parsed.password) == 'xek-admin?secret'
    assert parsed.username == 'bot_user'
    assert parsed.path == '/ai_interviewer'
