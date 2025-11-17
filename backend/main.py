import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from backend.db.session import get_db
from backend.services.habit_service import HabitService

from .api.v1.router import router as v1_router
from .core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle."""

    async def schedule_habit_transfer():
        """Schedule daily habit transfer."""
        async with get_db() as db:
            habit_service = HabitService(db)
            scheduler.add_job(habit_service.transfer_habits, "cron", hour=0, minute=0)
        scheduler.start()
        logger.info("Habit transfer scheduled at 00:00 daily")

    asyncio.create_task(schedule_habit_transfer())
    yield
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


app = FastAPI(
    title="Habit Tracker API",
    version="1.0.0",
    description="Backend API for Habit Tracker Bot",
    debug=settings.debug,
    openapi_tags=[
        {
            "name": "habits",
            "description": "CRUD for the Habit entity.",
        },
        {
            "name": "users",
            "description": "Telegram user authentication and management.",
        },
    ],
)


app.include_router(router=v1_router)


@app.get("/")
def read_root():
    return {"message": "Habit Tracker API is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
