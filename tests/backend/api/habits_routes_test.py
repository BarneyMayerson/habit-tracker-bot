import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.habits_routes
class TestHabitsRoutes:
    async def test_get_all_habits_empty(self, client: AsyncClient):
        response = await client.get("/habits")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
