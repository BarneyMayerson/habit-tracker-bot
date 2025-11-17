from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.habit import Habit
from backend.schemas.habit import HabitCreate, HabitResponse, HabitUpdate


class HabitService:
    """Service for habit business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_habits(self) -> list[HabitResponse]:
        """Get all habits."""
        result = await self.db.execute(select(Habit))
        habits = result.scalars().all()
        return [HabitResponse.model_validate(habit) for habit in habits]

    async def get_all_active_habits(self) -> list[HabitResponse]:
        """Get all active habits."""
        result = await self.db.execute(select(Habit).where(Habit.is_active))
        habits = result.scalars().all()
        return [HabitResponse.model_validate(habit) for habit in habits]

    async def get_habit_by_id(self, habit_id: int) -> HabitResponse | None:
        """Get habit by ID."""
        result = await self.db.execute(select(Habit).where(Habit.id == habit_id))
        habit = result.scalar_one_or_none()
        return HabitResponse.model_validate(habit) if habit else None

    async def create_habit(self, habit_data: HabitCreate, user_id: int) -> HabitResponse:
        """Create a new habit."""
        habit = Habit(
            title=habit_data.title,
            description=habit_data.description,
            user_id=user_id,
            is_active=True,
            completion_count=0,
            last_completed=None,
        )
        self.db.add(habit)
        await self.db.flush()
        await self.db.refresh(habit)
        return HabitResponse.model_validate(habit)

    async def update_habit(self, habit_id: int, habit_data: HabitUpdate) -> HabitResponse | None:
        """Update an existing habit."""

        result = await self.db.execute(select(Habit).where(Habit.id == habit_id))
        habit = result.scalar_one_or_none()
        if not habit:
            return None

        update_data = habit_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(habit, key, value)

        await self.db.flush()
        await self.db.refresh(habit, attribute_names=["updated_at"])
        return HabitResponse.model_validate(habit)

    async def delete_habit(self, habit_id: int) -> bool:
        """Delete habit by ID. Returns True if deleted, False if not found."""
        result = await self.db.execute(select(Habit).where(Habit.id == habit_id))
        habit = result.scalar_one_or_none()

        if not habit:
            return False

        await self.db.delete(habit)
        await self.db.flush()
        return True

    async def complete_habit(self, habit_id: int) -> HabitResponse | None:
        """Mark a habit as completed, increment completion_count and update last_completed."""
        result = await self.db.execute(select(Habit).where(Habit.id == habit_id))
        habit = result.scalar_one_or_none()

        if not habit:
            return None

        now = datetime.now(UTC)
        if habit.last_completed and habit.last_completed.date() == now.date():
            msg = "Habit already completed today"
            raise ValueError(msg)

        habit.completion_count += 1
        habit.last_completed = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(habit, attribute_names=["updated_at"])
        return HabitResponse.model_validate(habit)

    async def transfer_habits(self) -> None:
        """Transfer active habits to the next day."""
        result = await self.db.execute(select(Habit).where(Habit.is_active))
        habits = result.scalars().all()
        today = datetime.now(UTC).date()

        for habit in habits:
            if habit.completion_count >= settings.habit_duration:
                habit.is_active = False
            elif habit.last_completed and habit.last_completed.date() < today:
                habit.last_completed = None
        await self.db.flush()
