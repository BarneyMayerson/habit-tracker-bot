from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class UserBase(BaseModel):
    """Base schema for user data."""

    telegram_id: int
    username: Annotated[str | None, StringConstraints(max_length=100)] = None
    first_name: Annotated[str | None, StringConstraints(max_length=100)] = None
    last_name: Annotated[str | None, StringConstraints(max_length=100)] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str
