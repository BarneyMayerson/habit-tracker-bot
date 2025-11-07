from typing import Annotated

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, StringConstraints


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

fake_habits_db: list[HabitResponse] = [
    HabitResponse(
        id=1,
        title="Drink water",
        description="Drink 2 liters of water per day",
        is_active=True,
        completion_count=15,
    ),
    HabitResponse(
        id=2,
        title="Reading",
        description="Read 10 pages per day",
        is_active=True,
        completion_count=8,
    ),
]


@router.get("/", response_model=list[HabitResponse])
def get_all_habits() -> list[HabitResponse]:
    """
    Retrieve a list of all active habits.

    Returns:
        A JSON list of habit objects.
    """
    return fake_habits_db


@router.get("/{habit_id}", response_model=HabitResponse)
def get_habit_by_id(habit_id: int) -> HabitResponse:
    """
    Retrieve a single habit by its ID.

    Args:
        habit_id: Unique identifier of the habit.

    Returns:
        The habit data if found.

    Raises:
        HTTPException: If no habit with the given ID exists.
    """
    for habit in fake_habits_db:
        if habit.id == habit_id:
            return habit

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Habit with id {habit_id} not found",
    )


@router.post("/", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(habit_data: HabitCreate) -> HabitResponse:
    """
    Create a new habit.

    Args:
        habit_data: Data required to create a habit (title, optional description).

    Returns:
        The created habit with assigned ID.
    """
    new_id = max((h.id for h in fake_habits_db), default=0) + 1
    new_habit = HabitResponse(
        id=new_id,
        title=habit_data.title,
        description=habit_data.description,
        is_active=True,
        completion_count=0,
    )
    fake_habits_db.append(new_habit)
    return new_habit
