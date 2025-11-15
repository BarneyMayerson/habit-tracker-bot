from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class HabitBase(BaseModel):
    """Base schema for habit data."""

    title: Annotated[str, StringConstraints(min_length=2, max_length=100, strip_whitespace=True)]
    description: Annotated[str | None, StringConstraints(max_length=500, strip_whitespace=True)] = None


class HabitCreate(HabitBase):
    """Schema for creating a new habit."""

    user_id: int


class HabitUpdate(BaseModel):
    """Schema for updating an existing habit."""

    title: Annotated[str, StringConstraints(min_length=2, max_length=100, strip_whitespace=True)] | None = None
    description: Annotated[str | None, StringConstraints(max_length=500, strip_whitespace=True)] = None
    is_active: bool | None = None


class HabitResponse(HabitBase):
    """Schema for habit response."""

    id: int
    user_id: int
    is_active: bool
    completion_count: int
    created_at: datetime
    updated_at: datetime
    last_completed: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
