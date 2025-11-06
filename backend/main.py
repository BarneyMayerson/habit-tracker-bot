from fastapi import FastAPI

from .core.config import settings

app = FastAPI(
    title="Habit Tracker API",
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/")
def read_root():
    return {"message": "Habit Tracker API is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
