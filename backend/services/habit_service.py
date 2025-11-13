from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.habit import Habit
from backend.schemas.habit import HabitCreate, HabitResponse


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

    async def create_habit(self, habit_data: HabitCreate) -> HabitResponse:
        """Create a new habit."""
        habit = Habit(**habit_data.model_dump())
        self.db.add(habit)
        await self.db.flush()
        await self.db.refresh(habit)
        return HabitResponse.model_validate(habit)
