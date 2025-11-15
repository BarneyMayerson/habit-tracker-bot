from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.core.config import settings
from backend.db.session import get_db
from backend.main import app
from backend.models.habit import Habit
from backend.models.user import User

TEST_DB_URL = settings.database_url.replace(settings.db_name, f"{settings.db_name}_test")


@pytest.fixture
async def async_engine():
    engine = create_async_engine(TEST_DB_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Фикстура сессии + автоматический откат после теста."""
    connection = await async_engine.connect()
    transaction = await connection.begin()

    # Создаем сессию, привязанную к нашей тестовой транзакции
    session = AsyncSession(bind=connection, expire_on_commit=False)

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """AsyncClient с подменённой зависимостью."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Фикстура для создания тестового пользователя."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Jane",
        last_name="Doe",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_habit(db_session: AsyncSession, test_user: User) -> Habit:
    """Фикстура для создания тестовой привычки."""
    habit = Habit(
        user_id=test_user.id,
        title="Test Habit",
        description="Test Description",
        is_active=True,
        completion_count=0,
        last_completed=None,
    )

    db_session.add(habit)
    await db_session.flush()
    await db_session.refresh(habit)
    return habit


@pytest.fixture
async def access_token(test_user: User, db_session: AsyncSession) -> str:
    """Фикстура JWT токена для test_user."""
    from backend.services.user_service import UserService

    user_service = UserService(db_session)
    return user_service.create_access_token(data={"sub": str(test_user.telegram_id)})


@pytest.fixture
async def test_habits(db_session: AsyncSession, test_user: User) -> list[Habit]:
    """Фикстура для создания нескольких тестовых привычек."""
    habits = [
        Habit(user_id=test_user.id, title="Habit 1", is_active=True),
        Habit(user_id=test_user.id, title="Habit 2", is_active=True),
        Habit(user_id=test_user.id, title="Habit 3", is_active=False),
    ]

    for habit in habits:
        db_session.add(habit)

    await db_session.flush()

    for habit in habits:
        await db_session.refresh(habit)

    return habits
