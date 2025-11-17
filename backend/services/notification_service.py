from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logger import app_logger as logger
from backend.models.habit import Habit
from backend.models.user import User


class NotificationService:
    """Service for sending habit reminders via Telegram."""

    def __init__(self, db: AsyncSession, bot_token: str):
        self.db = db
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def _send_message(self, chat_id: int, text: str) -> bool:
        """Send a single message via Telegram Bot API."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Reminder sent → telegram_id={chat_id}")
                    return True
                logger.error(f"Telegram error {response.status_code}: {response.text} | user {chat_id}")
                return False
        except Exception as exc:
            logger.exception(f"Failed to send message to {chat_id}: {exc}")
            return False

    async def send_daily_reminders(self) -> None:
        """Send morning reminders about incomplete habits."""
        logger.info("Starting daily reminders job")
        today = datetime.now(UTC).date()

        stmt = (
            select(User, Habit)
            .join(Habit, User.id == Habit.user_id)
            .where(User.is_active.is_(True), Habit.is_active.is_(True))
        )

        result = await self.db.execute(stmt)
        reminders: dict[int, list[str]] = {}

        for user, habit in result:
            if not habit.last_completed or habit.last_completed.date() != today:
                reminders.setdefault(user.telegram_id, []).append(f"-- {habit.title}")

        if not reminders:
            logger.info("No reminders to send today")
            return

        sent_count = 0
        for telegram_id, habits in reminders.items():
            count = len(habits)
            text = (
                f"Good morning!\n\n"
                f"You have <b>{count}</b> habit{'s' if count > 1 else ''} to complete today:\n\n"
                + "\n".join(habits)
                + "\n\nHave a productive day!"
            )
            if await self._send_message(telegram_id, text):
                sent_count += 1

        logger.success(f"Daily reminders completed: {sent_count}/{len(reminders)} users notified")
