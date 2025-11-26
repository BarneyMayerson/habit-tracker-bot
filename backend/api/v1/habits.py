from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.session import get_db
from backend.schemas.habit import HabitCreate, HabitResponse, HabitUpdate
from backend.schemas.user import UserResponse
from backend.services.habit_service import HabitService
from backend.services.notification_service import NotificationService
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
    Retrieve a list of all habits.
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


@router.get("/stats")
async def get_habits_stats(
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> JSONResponse:
    """_summary_
    Get comprehensive statistics about user's habits.

    Includes:
    - Total active habits
    - Completions today / this week / all time
    - Current streak (days with at least one completion)
    - Best performing habit

    Requires Bearer token in Authorization header.

    Returns:
        JSON object with detailed statistics.
    """
    user_id = current_user.id
    today = datetime.now(UTC).date()
    week_ago = today - timedelta(days=7)

    all_habits = await habit_service.get_all_habits()
    user_habits = [h for h in all_habits if h.user_id == user_id]

    if not user_habits:
        return {
            "total_active_habits": 0,
            "completed_today": 0,
            "completed_this_week": 0,
            "total_completions_all_time": 0,
            "current_streak_days": 0,
            "best_habit": None,
            "best_habit_count": 0,
        }

    completed_today = sum(1 for h in user_habits if h.last_completed and h.last_completed.date() == today)
    completed_week = sum(1 for h in user_habits if h.last_completed and h.last_completed.date() >= week_ago)
    total_completions = sum(h.completion_count for h in user_habits)
    best_habit = max(user_habits, key=lambda h: h.completion_count, default=None)

    # Стрик — сколько дней подряд было хотя бы одно выполнение
    streak = 0
    check_date = today
    while True:
        has_completion = any(h.last_completed and h.last_completed.date() == check_date for h in user_habits)
        if has_completion:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return {
        "total_active_habits": len(user_habits),
        "completed_today": completed_today,
        "completed_this_week": completed_week,
        "total_completions_all_time": total_completions,
        "current_streak_days": streak,
        "best_habit": best_habit.title if best_habit else None,
        "best_habit_count": best_habit.completion_count if best_habit else 0,
    }


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


# TODO: the routes below should be removed in production
@router.post("/transfer")
async def transfer_habits(
    habit_service: Annotated[HabitService, Depends(get_habit_service)],
):
    """Manually trigger habit transfer."""
    await habit_service.transfer_habits()
    return {"message": "Habits transferred"}


@router.post("/debug/notify")
async def debug_notify():
    db = await anext(get_db())
    service = NotificationService(db, settings.telegram_bot_token)
    await service.send_daily_reminders()
    return {"status": "reminders sent"}
