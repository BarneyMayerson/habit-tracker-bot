from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.db.session import get_db
from backend.main import app
from backend.models.user import User

TEST_DB_URL = settings.database_url.replace(settings.db_name, f"{settings.db_name}_test")
test_engine = create_async_engine(TEST_DB_URL, echo=True)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Одна сессия + одна транзакция на тест."""
    async with TestSession() as session:  # noqa: SIM117
        async with session.begin():
            yield session


@pytest.fixture(autouse=True)
async def clean_tables(db_session: AsyncSession):
    """Автоматическая очистка всех таблиц перед каждым тестом."""
    # Используем отдельную сессию для очистки - это важно!
    async with TestSession() as cleanup_session:  # noqa: SIM117
        async with cleanup_session.begin():
            await cleanup_session.execute(text("TRUNCATE TABLE habits RESTART IDENTITY CASCADE"))
            await cleanup_session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Фикстура для создания тестового пользователя."""
    user = User(telegram_id=123456789, username="testuser", first_name="Jane", last_name="Doe")
    db_session.add(user)
    await db_session.flush()  # ВАЖНО! Сохраняем изменения, но не закрываем транзакцию
    await db_session.refresh(user)
    return user


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """AsyncClient с подменённой зависимостью."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
