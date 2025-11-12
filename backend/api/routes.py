from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.db.session import get_db
from backend.models.habit import Habit


class HabitCreate(BaseModel):
    """Schema for creating a new habit."""

    title: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    description: str | None = None


class HabitResponse(BaseModel):
    """Schema for habit response."""

    id: int
    title: str
    description: str | None = None
    is_active: bool
    completion_count: int

    model_config = {"from_attributes": True}


router = APIRouter(
    prefix="/habits",
    tags=["habits"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


@router.get("", response_model=list[HabitResponse])
async def get_all_habits(db: Annotated[AsyncSession, Depends(get_db)]) -> list[HabitResponse]:
    """
    Retrieve a list of all active habits.

    Returns:
        A JSON list of habit objects.
    """
    result = await db.execute(select(Habit).where(Habit.is_active))
    habits = result.scalars().all()
    return [HabitResponse.model_validate(habit) for habit in habits]
