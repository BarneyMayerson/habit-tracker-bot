from fastapi import status
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")

    assert response.status_code == status.HTTP_200_OK

    json_data = response.json()

    assert "message" in json_data
    assert json_data["message"] == "Habit Tracker API is running!"


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
