import pytest
from fastapi import status
from httpx import AsyncClient

from backend.models.habit import Habit
from backend.models.user import User


@pytest.mark.habits_routes
class TestHabitsRoutes:
    """Test cases for habits endpoints."""

    async def test_get_all_habits_empty(self, client: AsyncClient):
        response = await client.get("/habits")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_get_all_active_habits(self, client: AsyncClient, test_habits: list[Habit]):
        """Test getting all active habits when habits exist."""
        response = await client.get("/habits")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == len(test_habits) - 1  # one of test habits is not active
        assert all("id" in habit for habit in data)
        assert all("title" in habit for habit in data)

    async def test_get_habit_by_id(self, client: AsyncClient, test_habit: Habit):
        """Test getting a specific habit by ID."""
        response = await client.get(f"/habits/{test_habit.id}")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == test_habit.id
        assert data["title"] == test_habit.title
        assert data["user_id"] == test_habit.user_id

    async def test_get_habit_by_id_not_found(self, client: AsyncClient):
        """Test getting non-existent habit returns 404."""
        response = await client.get("/habits/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_habit_success(self, client: AsyncClient, test_user: User):
        """Test creating a new habit."""
        habit_data = {
            "title": "Test Habit",
            "description": "Test Description",
            "user_id": test_user.id,
        }
        response = await client.post("/habits", json=habit_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["title"] == habit_data["title"]
        assert data["description"] == habit_data["description"]
        assert data["user_id"] == habit_data["user_id"]
        assert "id" in data
