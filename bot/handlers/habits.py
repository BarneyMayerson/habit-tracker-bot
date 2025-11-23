from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import Message

from bot.api.client import APIClient
from bot.logger import log

router = Router(name="habits")


@router.message(F.text == "My Habits")
async def cmd_my_habits(message: Message, api: APIClient):
    """Handle 'My Habits' button press."""
    log.info(f"User {message.from_user.id} requested their habits list")

    if not api:
        await message.answer(
            "Session expired. Please re-authorize using /start",
            reply_markup=None,
        )
        return

    try:
        habits = api.get_active_habits()
        log.debug(f"Loaded {len(habits)} active habits")
    except Exception:
        log.exception("Failed to load habits")
        await message.answer("Error loading habits. Try again later.")
        return

    if not habits:
        await message.answer(
            "You don't have any habits yet!\n\nClick <b>Add Habit</b> to create your first one.",
            reply_markup=None,
        )
        return

    lines = ["<b>Your Habits</b>\n"]
    for i, habit in enumerate(habits, 1):
        title = habit["title"]
        description = habit.get("description", "")
        count = habit.get("completion_count", 0)

        last_completed = habit.get("last_completed")
        today_str = datetime.now(tz=UTC).date()
        status_emoji = "Completed" if last_completed and last_completed.startswith(today_str) else "Pending"

        lines.append(f"{status_emoji} <b>{title}</b>")
        if description:
            short_desc = description[:70] + "..." if len(description) > 70 else description
            lines.append(f"   {short_desc}")
        lines.append(f"   Completed: {count} time{'s' if count != 1 else ''}\n")

    text = "\n".join(lines)

    await message.answer(text, reply_markup=None)
