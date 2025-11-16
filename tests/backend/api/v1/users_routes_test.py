import pytest
from fastapi import status
from httpx import AsyncClient

from backend.models.user import User


@pytest.mark.users_routes
class TestUsersRoutes:
    """Test cases for habits endpoints."""

    async def test_telegram_auth_success(self, client: AsyncClient, test_user: User) -> None:
        """Test Telegram authentication with auth_token."""
        auth_data = {"telegram_id": test_user.telegram_id, "auth_token": test_user.auth_token}
        response = await client.post("/v1/users/telegram-auth", json=auth_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_telegram_auth_invalid_token(self, client: AsyncClient, test_user: User) -> None:
        """Test Telegram authentication with invalid auth_token."""
        auth_data = {"telegram_id": test_user.telegram_id, "auth_token": "wrong-token"}
        response = await client.post("/v1/users/telegram-auth", json=auth_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Invalid telegram_id or auth_token"}
