from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Telegram Bot app settings using pydantic-settings.
    All values are loaded from environment variables or .env file.
    """

    telegram_bot_token: str
    api_base_url: str = "http://backend:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


@cache
def get_settings() -> Settings:
    return Settings()
