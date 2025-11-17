from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.habit import HabitCreate, HabitResponse, HabitUpdate
from backend.schemas.user import UserResponse
from backend.services.habit_service import HabitService
from backend.services.user_service import UserService

router = APIRouter(
    prefix="/habits",
    tags=["habits"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/users/telegram-auth")


async def get_habit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> HabitService:
    """Dependency to provide HabitService with database session."""
    return HabitService(db)


async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Dependency to provide UserService with database session."""
    return UserService(db)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Get the current authenticated user."""
    return await user_service.get_current_user(token)


@router.get("", response_model=list[HabitResponse], status_code=status.HTTP_200_OK)
async def get_all_habits(
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[HabitResponse]:
    """
    Retrieve a list of all active habits.
    Requires Bearer token in Authorization header.

    Returns:
        A JSON list of habit objects.
    """
    result = await habit_service.get_all_habits()
    return [habit for habit in result if habit.user_id == current_user.id]


@router.get("/active", response_model=list[HabitResponse], status_code=status.HTTP_200_OK)
async def get_all_active_habits(
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> list[HabitResponse]:
    """
    Get all active habits for the current user.
    Requires Bearer token in Authorization header.
    """
    result = await habit_service.get_all_active_habits()
    return [habit for habit in result if habit.user_id == current_user.id]


@router.get("/{habit_id}", response_model=HabitResponse, status_code=status.HTTP_200_OK)
async def get_habit_by_id(
    habit_id: int,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> HabitResponse:
    """
    Retrieve a specific habit by ID.
    Requires Bearer token in Authorization header.

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
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this habit")
    return habit


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    habit_data: HabitCreate,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> HabitResponse:
    """
    Create a new habit.
    Requires Bearer token in Authorization header.

    Args:
        habit_data: The habit data to create.

    Returns:
        The created habit object.
    """
    return await habit_service.create_habit(habit_data, current_user.id)


@router.patch("/{habit_id}", response_model=HabitResponse, status_code=status.HTTP_200_OK)
async def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    """
    Update an existing habit with partial data.
    Requires Bearer token in Authorization header.

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
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this habit")
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(
    habit_id: int,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> None:
    """
    Delete a habit by its ID.
    Requires Bearer token in Authorization header.

    Args:
        habit_id: The ID of the habit to delete.

    Returns:
        None (204 No Content response).

    Raises:
        HTTPException: If the habit with the specified ID is not found (404).
    """
    habit = await habit_service.get_habit_by_id(habit_id)
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this habit")
    await habit_service.delete_habit(habit_id)


@router.post(
    "/{habit_id}/complete",
    response_model=HabitResponse,
    responses={422: {"description": "Habit already completed today"}},
    status_code=status.HTTP_200_OK,
)
async def complete_habit(
    habit_id: int,
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> HabitResponse:
    """
    Mark a habit as completed.
    Requires Bearer token in Authorization header.
    """
    habit = await habit_service.get_habit_by_id(habit_id)
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to complete this habit")

    try:
        return await habit_service.complete_habit(habit_id)
    except ValueError as ex:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(ex)) from ex


@router.post("/transfer")
async def transfer_habits(
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
):
    """Manually trigger habit transfer."""
    await habit_service.transfer_habits()
    return {"message": "Habits transferred"}
