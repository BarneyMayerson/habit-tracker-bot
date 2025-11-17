from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.schemas.user import UserCreate
from backend.services.user_service import UserService


@pytest.fixture
def mock_db_session() -> AsyncGenerator[AsyncMock]:
    """Mocked AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    yield session


@pytest.fixture
def user_service(mock_db_session: AsyncMock) -> UserService:
    """UserService with mocked DB session."""
    return UserService(db=mock_db_session)


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data."""
    return {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Jane",
        "last_name": "Doe",
    }


@pytest.mark.user_service
class TestUserService:
    """Unit tests for UserService."""

    async def test_get_or_create_user_new(
        self, user_service: UserService, mock_db_session: AsyncMock, sample_user_data: dict
    ) -> None:
        """Test creating a new user."""
        user_data = UserCreate(**sample_user_data)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Пользователь не существует
        mock_db_session.execute.return_value = mock_result
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()

        # Настраиваем refresh, чтобы он обновлял mock_user
        async def refresh_side_effect(user, attribute_names=None):
            user.id = 1
            user.is_active = True
            user.created_at = datetime.now(UTC)
            user.updated_at = datetime.now(UTC)
            user.auth_token = "test-auth-token"

        mock_db_session.refresh.side_effect = refresh_side_effect

        result = await user_service.get_or_create_user(user_data)

        assert result.telegram_id == user_data.telegram_id
        assert result.id == 1
        assert result.is_active is True
        assert result.auth_token == "test-auth-token"
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    async def test_authenticate_telegram_user_success(
        self, user_service: UserService, mock_db_session: AsyncMock, sample_user_data: dict
    ) -> None:
        """Test authenticating a Telegram user."""
        mock_user = User(**sample_user_data, is_active=True, auth_token="test-auth-token")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_service.authenticate_telegram_user(sample_user_data["telegram_id"], "test-auth-token")

        assert result.access_token is not None
        assert result.token_type == "bearer"

    async def test_authenticate_telegram_user_not_found(
        self, user_service: UserService, mock_db_session: AsyncMock
    ) -> None:
        """Test authenticating a non-existent Telegram user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await user_service.authenticate_telegram_user(999999999, "some-token")
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid telegram_id or auth_token"

    async def test_authenticate_telegram_user_invalid_token(
        self, user_service: UserService, mock_db_session: AsyncMock, sample_user_data: dict
    ) -> None:
        """Test authenticating with invalid auth_token."""
        mock_user = User(**sample_user_data, is_active=True, auth_token="test-auth-token")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc:
            await user_service.authenticate_telegram_user(sample_user_data["telegram_id"], "wrong-token")
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid telegram_id or auth_token"
