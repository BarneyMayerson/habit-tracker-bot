from fastapi import FastAPI

from .api.v1.habits import router as habit_router
from .core.config import settings

app = FastAPI(
    title="Habit Tracker API",
    version="1.0.0",
    description="Backend API for Habit Tracker Bot",
    debug=settings.debug,
)

app.include_router(router=habit_router)


@app.get("/")
def read_root():
    return {"message": "Habit Tracker API is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
