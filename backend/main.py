from fastapi import FastAPI

from backend.api.v1.router import router as v1_router
from backend.core.config import settings
from backend.core.lifespan import lifespan

app = FastAPI(
    title="Habit Tracker API",
    version="1.0.0",
    description="Backend API for Habit Tracker Bot",
    debug=settings.debug,
    lifespan=lifespan,
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
