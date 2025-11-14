from fastapi import APIRouter

from backend.api.v1.habits import router as habits_router

router = APIRouter(prefix="/v1")
router.include_router(habits_router)
