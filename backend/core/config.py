from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    FastAPI app settings using pydantic-settings.
    All values are loaded from environment variables or .env file.
    """

    db_connection: str = "postgresql+asyncpg"
    db_username: str = "user"
    db_password: str
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "database"

    debug: bool = False

    secret_key: str

    habit_duration: int = 21

    telegram_bot_token: str

    @property
    def database_url(self) -> str:
        return (
            f"{self.db_connection}://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


settings = Settings()
