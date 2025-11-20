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
    def __init__(self, token: str | None = None):
        self.base_url = settings.api_base_url
        self.token = token
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=10.0,
        )

    def _handle_response(self, response: httpx.Response) -> Any:
        """Centralized HTTP status code handling with custom exception mapping."""
        response_status = response.status_code

        if response_status == status.HTTP_200_OK or response_status == status.HTTP_201_CREATED:
            return response.json() if response.content else None

        if response_status == status.HTTP_204_NO_CONTENT:
            return None

        if response_status == status.HTTP_401_UNAUTHORIZED:
            raise AuthorizationError()

        if response_status == status.HTTP_403_FORBIDDEN:
            msg = "Forbidden"
            raise AuthenticationError(msg)

        if response_status == status.HTTP_404_NOT_FOUND:
            raise NotFoundError()

        if response_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
            detail = response.json().get("detail", "")
            if isinstance(detail, str) and "already completed today" in detail.lower():
                raise HabitAlreadyCompletedError()
            raise ValidationError(detail)

        if status.HTTP_500_INTERNAL_SERVER_ERROR <= response_status < 600:
            raise ServerError(response.text)

        response.raise_for_status()
        return None

    def request(self, method: str, endpoint: str, **kwargs):
        response = self.client.request(method, endpoint, **kwargs)
        return self._handle_response(response)

    def auth_telegram(self, telegram_id: int, auth_token: str):
        """Authenticate user via Telegram Login Widget data and return JWT access token."""
        response = httpx.post(
            f"{self.base_url}/v1/users/telegram-auth",
            json={"telegram_id": telegram_id, "auth_token": auth_token},
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get_active_habits(self):
        """Fetch all currently active habits for the authenticated user."""
        return self.request("GET", "/v1/habits/active")

    def create_habit(self, title: str, description: str | None):
        """Create a new habit and return its full representation."""
        return self.request("POST", "/v1/habits", json={"title": title, "description": description})

    def complete_habit(self, habit_id: int):
        """Mark habit as completed for today and return updated habit data."""
        return self.request("POST", f"/v1/habits/{habit_id}/complete")

    def get_habit(self, habit_id: int) -> dict:
        return self.request("GET", f"/v1/habits/{habit_id}")

    def update_habit(self, habit_id: int, **kwargs) -> dict:
        """Partially update habit fields and return the updated object."""
        return self.request("PATCH", f"/v1/habits/{habit_id}", json=kwargs)

    def delete_habit(self, habit_id: int) -> None:
        """Permanently delete a habit."""
        return self.request("DELETE", f"/v1/habits/{habit_id}")
