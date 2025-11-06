from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FastAPI app settings."""

    app_host: str = "127.0.0.1"
    app_port: str = "8000"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


settings = Settings()
