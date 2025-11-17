from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.habit import Habit
from backend.schemas.habit import HabitCreate, HabitUpdate
from backend.services.habit_service import HabitService


@pytest.fixture
def mock_db_session() -> AsyncGenerator[AsyncMock]:
    """Mocked AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    # Имитируем поведение flush и refresh
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    yield session


@pytest.fixture
def habit_service(mock_db_session: AsyncMock) -> HabitService:
    """HabitService with mocked DB session."""
    return HabitService(db=mock_db_session)


@pytest.fixture
def sample_habit_data() -> dict:
    """Sample habit data."""
    return {
        "id": 1,
        "user_id": 100,
        "title": "Test Habit",
        "description": "Test Description",
        "is_active": True,
        "completion_count": 5,
        "created_at": datetime.fromisoformat("2025-11-05T10:00:00+00:00"),
        "updated_at": datetime.fromisoformat("2025-11-05T10:00:00+00:00"),
        "last_completed": None,
    }


@pytest.fixture
def db_habit(sample_habit_data: dict) -> Habit:
    """Mocked Habit ORM instance."""
    return Habit(**sample_habit_data)


@pytest.mark.habit_service
class TestHabitService:
    """Unit tests for HabitService."""

    async def test_get_all_active_habits(
        self, habit_service: HabitService, mock_db_session: AsyncMock, db_habit: Habit
    ) -> None:
        """Should return list of active habits."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [db_habit]
        mock_db_session.execute.return_value = mock_result

        result = await habit_service.get_all_active_habits()

        assert len(result) == 1
        assert result[0].title == "Test Habit"
        assert result[0].completion_count == 5

    async def test_get_habit_by_id_found(
        self, habit_service: HabitService, mock_db_session: AsyncMock, db_habit: Habit
    ) -> None:
        """Should return habit when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_habit
        mock_db_session.execute.return_value = mock_result

        result = await habit_service.get_habit_by_id(habit_id=1)

        assert result is not None
        assert result.id == 1
        assert result.title == "Test Habit"

    async def test_get_habit_by_id_not_found(self, habit_service: HabitService, mock_db_session: AsyncMock) -> None:
        """Should return None when habit not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await habit_service.get_habit_by_id(habit_id=999)

        assert result is None

    async def test_create_habit(self, habit_service: HabitService, mock_db_session: AsyncMock) -> None:
        """Should create and return new habit."""
        from datetime import datetime

        create_data = HabitCreate(title="New Habit")

        # Настройка моков для сессии
        mock_db_session.add = MagicMock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Определяем ожидаемую дату для created_at и updated_at
        expected_datetime = datetime(2025, 11, 5, 10, 0, tzinfo=UTC)

        # Настройка refresh для эмуляции присвоения всех полей
        def refresh_side_effect(obj):
            obj.id = 2
            obj.is_active = True
            obj.completion_count = 0
            obj.created_at = expected_datetime
            obj.updated_at = expected_datetime

        mock_db_session.refresh.side_effect = refresh_side_effect

        # Вызов метода
        result = await habit_service.create_habit(create_data, 100)

        # Проверки результата
        assert result.title == "New Habit"
        assert result.user_id == 100
        assert result.is_active is True
        assert result.completion_count == 0
        assert result.created_at == expected_datetime
        assert result.updated_at == expected_datetime
        assert result.description is None
        assert result.id == 2

        # Проверки вызовов методов сессии
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    async def test_update_habit(self, habit_service: HabitService, mock_db_session: AsyncMock, db_habit: Habit) -> None:
        """Should update and return existing habit."""
        update_data = HabitUpdate(title="Updated Habit", is_active=False)

        # Настройка мока для поиска привычки
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_habit
        mock_db_session.execute.return_value = mock_result

        # Настройка мока для refresh
        expected_datetime = datetime(2025, 11, 6, 12, 0, tzinfo=UTC)

        def refresh_side_effect(obj, attribute_names=None):
            obj.updated_at = expected_datetime

        mock_db_session.refresh.side_effect = refresh_side_effect

        # Вызов метода
        result = await habit_service.update_habit(habit_id=1, habit_data=update_data)

        # Проверки результата
        assert result is not None
        assert result.id == 1
        assert result.title == "Updated Habit"
        assert result.is_active is False
        assert result.description == "Test Description"  # не изменено
        assert result.completion_count == 5  # не изменено
        assert result.updated_at == expected_datetime

        # Проверки вызовов методов сессии
        mock_db_session.execute.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    async def test_update_habit_not_found(self, habit_service: HabitService, mock_db_session: AsyncMock) -> None:
        """Should return None when habit not found."""
        update_data = HabitUpdate(title="Updated Habit")

        # Настройка мока для отсутствия привычки
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Вызов метода
        result = await habit_service.update_habit(habit_id=999, habit_data=update_data)

        # Проверки результата
        assert result is None
        mock_db_session.execute.assert_called_once()
        mock_db_session.flush.assert_not_called()
        mock_db_session.refresh.assert_not_called()

    async def test_delete_habit(self, habit_service: HabitService, mock_db_session: AsyncMock, db_habit: Habit) -> None:
        """Should delete existing habit and return True."""
        # Мокаем поиск привычки
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_habit
        mock_db_session.execute.return_value = mock_result

        # Мокаем delete и commit
        mock_db_session.delete = AsyncMock()
        mock_db_session.flush = AsyncMock()

        # Выполняем удаление
        result = await habit_service.delete_habit(habit_id=1)

        # Проверяем результат
        assert result is True

        # Проверяем вызовы
        mock_db_session.execute.assert_called_once()
        mock_db_session.delete.assert_called_once_with(db_habit)
        mock_db_session.flush.assert_called_once()

    async def test_delete_habit_not_found(self, habit_service: HabitService, mock_db_session: AsyncMock) -> None:
        """Should return False when habit not found."""
        # Мокаем отсутствие привычки
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Мокаем delete и commit (не должны вызываться)
        mock_db_session.delete = AsyncMock()
        mock_db_session.flush = AsyncMock()

        # Выполняем удаление
        result = await habit_service.delete_habit(habit_id=999)

        # Проверяем результат
        assert result is False

        # Проверяем, что delete и commit НЕ вызывались
        mock_db_session.execute.assert_called_once()
        mock_db_session.delete.assert_not_called()
        mock_db_session.flush.assert_not_called()

    async def test_complete_habit_success(
        self, habit_service: HabitService, mock_db_session: AsyncMock, db_habit: Habit
    ) -> None:
        """Test marking a habit as completed."""
        # Мокаем результат запроса
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_habit
        mock_db_session.execute.return_value = mock_result

        # Мокаем flush и refresh
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Выполняем complete_habit
        initial_count = db_habit.completion_count
        result = await habit_service.complete_habit(habit_id=db_habit.id)

        # Проверяем результат
        assert result is not None
        assert result.id == db_habit.id
        assert result.completion_count == initial_count + 1
        assert result.last_completed is not None
        assert isinstance(result.last_completed, datetime)
        assert result.updated_at >= db_habit.updated_at

        # Проверяем вызовы
        mock_db_session.execute.assert_called_once()
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(db_habit, attribute_names=["updated_at"])

    async def test_complete_habit_already_completed_today(
        self, habit_service: HabitService, mock_db_session: AsyncMock, db_habit: Habit
    ) -> None:
        """Test attempting to complete a habit already completed today."""
        db_habit.last_completed = datetime.now(UTC)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_habit
        mock_db_session.execute.return_value = mock_result
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        with pytest.raises(ValueError, match="Habit already completed today"):
            await habit_service.complete_habit(habit_id=db_habit.id)

        mock_db_session.execute.assert_called_once()
        mock_db_session.flush.assert_not_called()
        mock_db_session.refresh.assert_not_called()

    async def test_complete_habit_not_found(self, habit_service: HabitService, mock_db_session: AsyncMock) -> None:
        """Test completing a non-existent habit."""
        # Мокаем отсутствие привычки
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Мокаем flush и refresh (не должны вызываться)
        mock_db_session.flush = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Выполняем complete_habit
        result = await habit_service.complete_habit(habit_id=999)

        # Проверяем результат
        assert result is None

        # Проверяем вызовы
        mock_db_session.execute.assert_called_once()
        mock_db_session.flush.assert_not_called()
        mock_db_session.refresh.assert_not_called()

    async def test_transfer_habits(self, habit_service: HabitService, mock_db_session: AsyncMock) -> None:
        yesterday = datetime.now(UTC) - timedelta(days=1)
        mock_habit_active = Habit(
            id=1,
            user_id=1,
            title="Active Habit",
            is_active=True,
            completion_count=5,
            last_completed=yesterday,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_habit_done = Habit(
            id=2,
            user_id=1,
            title="Done Habit",
            is_active=True,
            completion_count=21,
            last_completed=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_habit_active, mock_habit_done]
        mock_db_session.execute.return_value = mock_result
        mock_db_session.flush = AsyncMock()

        await habit_service.transfer_habits()

        assert mock_habit_active.is_active is True
        assert mock_habit_active.last_completed is None
        assert mock_habit_done.is_active is False
        mock_db_session.flush.assert_called_once()
