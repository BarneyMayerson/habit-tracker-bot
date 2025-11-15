from fastapi import APIRouter

from backend.api.v1.habits import router as habits_router
from backend.api.v1.users import router as users_router

router = APIRouter(prefix="/v1")
router.include_router(habits_router)
router.include_router(users_router)
