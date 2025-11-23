from typing import Any

import httpx
from fastapi import status

from bot.config import get_settings
from bot.exceptions import (
    AuthenticationError,
    AuthorizationError,
    HabitAlreadyCompletedError,
    NotFoundError,
    ServerError,
    ValidationError,
)

settings = get_settings()


class APIClient:
    """Fully asynchronous HTTP client for FastAPI backend."""

    def __init__(self, token: str | None = None):
        self.base_url = settings.api_base_url
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=10.0,
        )

    async def _handle_response(self, response: httpx.Response) -> Any:
        """Centralized HTTP status code handling with custom exception mapping."""
        status_code = response.status_code

        if status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            return response.json() if response.content else None
        if status_code == status.HTTP_204_NO_CONTENT:
            return None

        if status_code == status.HTTP_401_UNAUTHORIZED:
            raise AuthorizationError()
        if status_code == status.HTTP_403_FORBIDDEN:
            raise AuthenticationError("Forbidden")
        if status_code == status.HTTP_404_NOT_FOUND:
            raise NotFoundError()
        if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            detail = response.json().get("detail", "")
            if isinstance(detail, str) and "already completed today" in detail.lower():
                raise HabitAlreadyCompletedError()
            raise ValidationError(detail)
        if status_code >= 500:
            raise ServerError(response.text)

        response.raise_for_status()
        return None

    async def request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Perform HTTP request and handle response."""
        response = await self.client.request(method, endpoint, **kwargs)
        return await self._handle_response(response)

    async def auth_telegram(self, telegram_id: int, auth_token: str) -> str:
        """Authenticate via Telegram and get JWT using the existing AsyncClient."""
        response = await self.client.post(
            "/v1/users/telegram-auth",
            json={"telegram_id": telegram_id, "auth_token": auth_token},
        )
        response.raise_for_status()
        return response.json()["access_token"]

    async def get_active_habits(self) -> list[dict]:
        """Fetch all active habits."""
        return await self.request("GET", "/v1/habits/active") or []

    async def create_habit(self, title: str, description: str | None = None) -> dict:
        return await self.request("POST", "/v1/habits", json={"title": title, "description": description})

    async def complete_habit(self, habit_id: int) -> dict:
        return await self.request("POST", f"/v1/habits/{habit_id}/complete")

    async def get_habit(self, habit_id: int) -> dict:
        return await self.request("GET", f"/v1/habits/{habit_id}")

    async def update_habit(self, habit_id: int, **kwargs) -> dict:
        return await self.request("PATCH", f"/v1/habits/{habit_id}", json=kwargs)

    async def delete_habit(self, habit_id: int) -> None:
        return await self.request("DELETE", f"/v1/habits/{habit_id}")

    async def close(self):
        """Close underlying HTTP connections."""
        await self.client.aclose()
