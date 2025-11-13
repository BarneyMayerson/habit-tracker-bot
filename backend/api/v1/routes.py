from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.habit import HabitCreate, HabitResponse
from backend.services.habit_service import HabitService

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
    service = HabitService(db)
    return await service.get_all_active_habits()


@router.get("/{habit_id}", response_model=HabitResponse)
async def get_habit_by_id(habit_id: int, db: Annotated[AsyncSession, Depends(get_db)]) -> HabitResponse:
    """
    Retrieve a specific habit by ID.

    Args:
        habit_id: The ID of the habit to retrieve.

    Returns:
        The habit object.

    Raises:
        HTTPException: If habit is not found.
    """
    service = HabitService(db)
    habit = await service.get_habit_by_id(habit_id)

    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Habit with ID {habit_id} not found")

    return habit


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(habit_data: HabitCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> HabitResponse:
    """
    Create a new habit.

    Args:
        habit_data: The habit data to create.

    Returns:
        The created habit object.
    """
    service = HabitService(db)
    return await service.create_habit(habit_data)
