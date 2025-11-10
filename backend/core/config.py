import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """FastAPI app settings."""

    db_conn: str = os.getenv("DB_CONNECTION", "postgresql+asyncpg")
    db_user: str = os.getenv("DB_USERNAME", "user")
    db_password: str = os.getenv("DB_PASSWORD", "password")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    db_name: str = os.getenv("DB_DATABASE", "database")
    test_db_url: str = os.getenv("TEST_DATABASE_URL", "")

    debug: bool = False

    @property
    def database_url_async(self) -> str:
        return f"{self.db_conn}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf8", extra="ignore")


settings = Settings()
