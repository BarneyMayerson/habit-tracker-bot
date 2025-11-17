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

scheduler = AsyncIOScheduler(timezone="UTC")


async def get_db_with_retry(retries: int = 5, delay: float = 2):
    """Wait for DB to become available."""
    for attempt in range(1, retries + 1):
        try:
            db = await anext(get_db())
            logger.info("Database connection established for scheduler")
            return db
        except Exception as e:
            if attempt == retries:
                logger.error(f"Failed to connect to DB after {retries} attempts")
                raise
            logger.warning(f"DB not ready (attempt {attempt}/{retries}): {e}")
            await asyncio.sleep(delay)
    return None


def _setup_scheduler_jobs(db_session):
    """Configure all scheduled jobs."""
    habit_service = HabitService(db_session)
    notification_service = NotificationService(db_session, settings.telegram_bot_token)

    scheduler.add_job(
        habit_service.transfer_habits,
        trigger="cron",
        hour=0,
        minute=0,
        id="transfer_habits",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        notification_service.send_daily_reminders,
        trigger="cron",
        hour=9,
        minute=0,
        id="send_daily_reminders",
        replace_existing=True,
        max_instances=1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle manager."""

    async def initialize_scheduler():
        db = await get_db_with_retry()
        _setup_scheduler_jobs(db)
        scheduler.start()
        logger.success("Scheduler started → transfer_habits (00:00 UTC), reminders (09:00 UTC)")

    task = asyncio.create_task(initialize_scheduler())
    task.add_done_callback(lambda t: t.result() if not t.cancelled() else None)

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
