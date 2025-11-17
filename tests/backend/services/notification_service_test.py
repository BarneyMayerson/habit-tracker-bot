from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.habit import Habit
from backend.models.user import User
from backend.services.notification_service import NotificationService


@pytest.fixture
def mock_db_session() -> AsyncGenerator[AsyncMock]:
    """Mocked AsyncSession."""
    session = AsyncMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    yield session


@pytest.fixture
def notification_service(mock_db_session: AsyncMock):
    return NotificationService(mock_db_session, "fake_token")


@pytest.mark.notification_service
class TestNotificationService:
    """Unit tests for NotificationService."""

    async def test_send_daily_reminders_no_habits(
        self, notification_service: NotificationService, mock_db_session: AsyncMock
    ):
        mock_db_session.execute.return_value = MagicMock(scalars=MagicMock(all=lambda: []))

        with patch.object(notification_service, "_send_message", new_callable=AsyncMock) as mock_send:
            await notification_service.send_daily_reminders()
            mock_send.assert_not_called()

    async def test_send_daily_reminders_one_user(
        self, notification_service: NotificationService, mock_db_session: AsyncMock
    ):
        yesterday = datetime.now(UTC) - timedelta(days=1)
        user = User(id=1, telegram_id=123456789, username="testuser", is_active=True)
        habit = Habit(id=1, user_id=1, title="Drink water", last_completed=yesterday, is_active=True)

        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([(user, habit)]))
        mock_db_session.execute.return_value = mock_result

        with patch.object(notification_service, "_send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            await notification_service.send_daily_reminders()
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            assert args[0] == 123456789
            assert "Drink water" in args[1]
            assert "Good morning" in args[1]
