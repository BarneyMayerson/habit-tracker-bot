from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.user import Token, UserCreate, UserResponse
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


class TelegramAuthRequest(BaseModel):
    """Request schema for Telegram authentication."""

    telegram_id: int
    auth_token: str


async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Dependency to provide HabitService with database session."""
    return UserService(db)


@router.post("/telegram-auth", response_model=Token)
async def telegram_auth(
    auth_data: TelegramAuthRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Token:
    """Authenticate a Telegram user and return a JWT token."""
    return await user_service.authenticate_telegram_user(auth_data.telegram_id, auth_data.auth_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Register or get a Telegram user."""
    return await user_service.get_or_create_user(user_data)
