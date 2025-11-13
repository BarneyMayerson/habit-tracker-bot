from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class HabitBase(BaseModel):
    """Base schema for habit data."""

    title: Annotated[str, StringConstraints(min_length=3, strip_whitespace=True)]
    description: str | None = None


class HabitCreate(HabitBase):
    """Schema for creating a new habit."""

    user_id: int


class HabitUpdate(BaseModel):
    """Schema for updating an existing habit."""

    title: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] | None = None
    description: str | None = None
    is_active: bool | None = None


class HabitResponse(HabitBase):
    """Schema for habit response."""

    id: int
    user_id: int
    is_active: bool
    completion_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
