import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from backend.core.config import settings
from backend.core.logger import app_logger as logger
from backend.db.session import get_db
from backend.services.habit_service import HabitService
from backend.services.notification_service import NotificationService

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle: start scheduler on startup, stop on shutdown."""

    # Startup: schedule habit transfer
    async def schedule_habit_transfer():
        db = await anext(get_db())
        habit_service = HabitService(db)
        scheduler.add_job(
            habit_service.transfer_habits,
            "cron",
            hour=0,
            minute=0,
            timezone="UTC",
            id="daily_reminders",
            replace_existing=True,
        )

        db_notify = await anext(get_db())
        notification_service = NotificationService(db_notify, settings.telegram_bot_token)
        scheduler.add_job(
            notification_service.send_daily_reminders,
            "cron",
            hour=9,
            minute=0,
            timezone="UTC",
            id="daily_reminders",
            replace_existing=True,
        )

        scheduler.start()
        logger.success("Scheduler started: habit_transfer (00:00) + daily_reminders (09:00 UTC)")

    task = asyncio.create_task(schedule_habit_transfer())

    try:
        yield
    finally:
        # Shutdown: stop scheduler
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")

        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
