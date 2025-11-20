import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.user import User
from backend.schemas.user import Token, UserCreate, UserResponse

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserService:
    """Service for Telegram user authentication and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(self, user_data: UserCreate) -> UserResponse:
        """Get or create a user by telegram_id."""
        result = await self.db.execute(select(User).where(User.telegram_id == user_data.telegram_id))
        user = result.scalar_one_or_none()

        print(user_data)
        print(user_data.first_name)

        if user:
            updated = False
            if user_data.username is not None and user.username != user_data.username:
                print("GET USERNAME")
                user.username = user_data.username
                updated = True
            if user_data.first_name is not None and user.first_name != user_data.first_name:
                print("GET FIRST_NAME")
                user.first_name = user_data.first_name
                updated = True
            if user_data.last_name is not None and user.last_name != user_data.last_name:
                print("GET LAST_NAME")
                user.last_name = user_data.last_name
                updated = True

            if updated:
                await self.db.flush()
                await self.db.refresh(user)
            return UserResponse.model_validate(user)

        user = User(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            auth_token=str(uuid.uuid4()),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + expires_delta if expires_delta else datetime.now(UTC) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)

    async def authenticate_telegram_user(self, telegram_id: int, auth_token: str) -> Token:
        """Authenticate a Telegram user and return a JWT token."""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id, User.auth_token == auth_token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid telegram_id or auth_token")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        # user.auth_token = None #TODO:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(data={"sub": str(user.telegram_id)}, expires_delta=access_token_expires)
        return Token(access_token=access_token, token_type="bearer")

    async def get_current_user(self, token: str) -> UserResponse:
        """Get the current user from a JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
            telegram_id: str | None = payload.get("sub")
            if telegram_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

        result = await self.db.execute(select(User).where(User.telegram_id == int(telegram_id)))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        return UserResponse.model_validate(user)
