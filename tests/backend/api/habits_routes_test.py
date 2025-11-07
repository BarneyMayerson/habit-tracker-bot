import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.main import app

client: TestClient = TestClient(app)


@pytest.mark.habits_routes
class TestHabitsRoutes:
    def test_get_all_habits(self) -> None:
        response = client.get("/habits")

        assert response.status_code == status.HTTP_200_OK

        habits = response.json()

        assert isinstance(habits, list)
        assert len(habits) > 0

        first = habits[0]

        assert "id" in first
        assert "title" in first
        assert "is_active" in first
        assert "completion_count" in first

    def test_get_habit_by_existing_id(self) -> None:
        response = client.get("/habits/1")

        assert response.status_code == status.HTTP_200_OK
        habit = response.json()
        assert habit["id"] == 1
        assert habit["title"] == "Drink water"

    def test_get_habit_by_nonexistent_id(self) -> None:
        response = client.get("/habits/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        detail = response.json()["detail"]

        assert "not found" in detail.lower()

    def test_create_habit_successfully(self) -> None:
        payload = {"title": "Morning run", "description": "Run 3 km every morning"}
        before_response = client.get("/habits")
        initial_count = len(before_response.json())

        response = client.post("/habits", json=payload)

        assert response.status_code == status.HTTP_201_CREATED

        created = response.json()

        assert created["title"] == payload["title"]
        assert created["description"] == payload["description"]
        assert isinstance(created["id"], int)
        assert created["completion_count"] == 0
        assert created["is_active"] is True

        after_response = client.get("/habits")
        final_count = len(after_response.json())

        assert final_count == initial_count + 1

    def test_create_habit_with_empty_title(self) -> None:
        payload = {"title": "", "description": "Invalid habit"}
        response = client.post("/habits", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_habit_with_whitespace_only_title(self) -> None:
        payload = {"title": "   ", "description": "Invalid"}
        response = client.post("/habits", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
