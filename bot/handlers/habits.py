from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import Message

from bot.api.client import APIClient
from bot.keyboards.inline.habits import get_habit_buttons, get_refresh_button
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
        habits = await api.get_active_habits()
        log.debug(f"Loaded {len(habits)} active habits")
    except Exception:
        log.exception("Failed to load habits")
        await message.answer("Error loading habits. Try again later.")
        return

    today_str = datetime.now(tz=UTC).date()
    for habit in habits:
        habit_id = habit["id"]
        title = habit["title"]
        description = habit.get("description", "")
        count = habit["completion_count"]
        last_completed_raw = habit.get("last_completed")
        last_completed = last_completed_raw[:10] if last_completed_raw else ""
        status = "Completed" if last_completed == today_str else "Pending"

        lines = [f"{status} <b>{title}</b>"]

        if description:
            short = description[:100] + ("..." if len(description) > 100 else "")
            lines.append(f"<i>{short}</i>")
        lines.append(f"Completed: {count} time{'s' if count != 1 else ''}")

        text = "\n".join(lines)
        kb = get_habit_buttons(habit_id=habit_id, completed_today=(last_completed == today_str))
        await message.answer(text, reply_markup=kb)

    await message.answer("↑ Your habits ↑", reply_markup=get_refresh_button())
