from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.user import Token, UserCreate, UserResponse
from backend.services.user_service import UserService

router = APIRouter(prefix="/v1/users", tags=["users"])


async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Dependency to provide HabitService with database session."""
    return UserService(db)


@router.post("/telegram-auth", response_model=Token)
async def telegram_auth(
    telegram_id: int,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Token:
    """Authenticate a Telegram user and return a JWT token."""
    return await user_service.authenticate_telegram_user(telegram_id)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Register or get a Telegram user."""
    return await user_service.get_or_create_user(user_data)
