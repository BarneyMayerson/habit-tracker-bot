from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.habit import HabitCreate, HabitResponse, HabitUpdate
from backend.services.habit_service import HabitService

router = APIRouter(
    prefix="/habits",
    tags=["habits"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


async def get_habit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> HabitService:
    """Dependency to provide HabitService with database session."""
    return HabitService(db)


@router.get("", response_model=list[HabitResponse], status_code=status.HTTP_200_OK)
async def get_all_habits(habit_service: Annotated[HabitService, Depends(get_habit_service)]) -> list[HabitResponse]:
    """
    Retrieve a list of all active habits.

    Returns:
        A JSON list of habit objects.
    """
    return await habit_service.get_all_habits()


@router.get("/{habit_id}", response_model=HabitResponse, status_code=status.HTTP_200_OK)
async def get_habit_by_id(
    habit_id: int,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
) -> HabitResponse:
    """
    Retrieve a specific habit by ID.

    Args:
        habit_id: The ID of the habit to retrieve.

    Returns:
        The habit object.

    Raises:
        HTTPException: If habit is not found.
    """
    habit = await habit_service.get_habit_by_id(habit_id)
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    return habit


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    habit_data: HabitCreate,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
) -> HabitResponse:
    """
    Create a new habit.

    Args:
        habit_data: The habit data to create.

    Returns:
        The created habit object.
    """
    return await habit_service.create_habit(habit_data)


@router.patch("/{habit_id}", response_model=HabitResponse, status_code=status.HTTP_200_OK)
async def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
):
    """
    Update an existing habit with partial data.

    Args:
        habit_id: The ID of the habit to update.
        habit_data: The data to update, with optional fields like title, description, or status.

    Returns:
        The updated habit object with all details, including updated timestamps.

    Raises:
        HTTPException: If the habit with the specified ID is not found (404).
    """
    habit = await habit_service.update_habit(habit_id, habit_data)
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(
    habit_id: int,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
) -> None:
    """
    Delete a habit by its ID.

    Args:
        habit_id: The ID of the habit to delete.

    Returns:
        None (204 No Content response).

    Raises:
        HTTPException: If the habit with the specified ID is not found (404).
    """
    deleted = await habit_service.delete_habit(habit_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Habit with ID {habit_id} not found")
