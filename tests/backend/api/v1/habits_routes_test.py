import pytest
from fastapi import status
from httpx import AsyncClient

from backend.models.habit import Habit
from backend.models.user import User


@pytest.mark.habits_routes
class TestHabitsRoutes:
    """Test cases for habits endpoints."""

    async def test_get_all_habits_empty(self, client: AsyncClient) -> None:
        response = await client.get("/habits")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    async def test_get_all_habits(self, client: AsyncClient, test_habits: list[Habit]) -> None:
        """Test getting all active habits when habits exist."""
        response = await client.get("/habits")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == len(test_habits)
        assert all("id" in habit for habit in data)
        assert all("title" in habit for habit in data)

    async def test_get_habit_by_id(self, client: AsyncClient, test_habit: Habit) -> None:
        """Test getting a specific habit by ID."""
        response = await client.get(f"/habits/{test_habit.id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == test_habit.id
        assert data["title"] == test_habit.title
        assert data["user_id"] == test_habit.user_id
        assert data["is_active"] is True
        assert data["completion_count"] == test_habit.completion_count
        assert data["description"] == test_habit.description

    async def test_get_habit_by_id_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent habit returns 404."""
        response = await client.get("/habits/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Habit not found"}

    async def test_create_habit_success(self, client: AsyncClient, test_user: User) -> None:
        """Test creating a new habit."""
        habit_data = {
            "title": "New Habit",
            "description": "Test description",
            "user_id": test_user.id,
        }
        response = await client.post("/habits", json=habit_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["title"] == "New Habit"
        assert data["user_id"] == test_user.id
        assert data["description"] == "Test description"
        assert data["is_active"] is True
        assert data["completion_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_update_habit(self, client: AsyncClient, test_habit: Habit) -> None:
        """Test updating an existing habit with partial data."""
        update_data = {"title": "Updated Habit", "is_active": False}
        response = await client.patch(f"habits/{test_habit.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == test_habit.id
        assert data["title"] == "Updated Habit"
        assert data["is_active"] is False
        assert data["user_id"] == test_habit.user_id
        assert data["completion_count"] == test_habit.completion_count
        assert data["description"] == test_habit.description

    async def test_update_habit_not_found(self, client: AsyncClient) -> None:
        """Test updating a habit that does not exist."""
        update_data = {"title": "Updated Habit"}
        response = await client.patch("habits/999", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Habit not found"}

    async def test_delete_habit(self, client: AsyncClient, test_habit: Habit) -> None:
        """Test deleting an existing habit."""
        response = await client.delete(f"/habits/{test_habit.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = await client.get(f"/habits/{test_habit.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_habit_not_found(self, client: AsyncClient) -> None:
        """Test deleting a habit that does not exist."""
        response = await client.delete("/habits/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "Habit with ID 999 not found"}
