from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.api.client import APIClient
from bot.exceptions import HabitAlreadyCompletedError
from bot.keyboards.inline.habits import get_habit_buttons, get_refresh_button
from bot.logger import log

router = Router(name="habits")


async def show_habits_list(target: Message | CallbackQuery, api: APIClient):
    try:
        habits = await api.get_active_habits()
        log.debug(f"Loaded {len(habits)} active habits")
    except Exception:
        log.exception("Failed to load habits")
        text = "Error loading habits"
        if isinstance(target, Message):
            await target.answer(text)
        else:
            await target.message.edit_text(text)
        return

    today_str = datetime.now(tz=UTC).date()

    if not habits:
        text = "You don't have any habits yet!\n\nClick <b>Add Habit</b> to create one."
        kb = get_refresh_button()
        if isinstance(target, Message):
            await target.answer(text, reply_markup=kb)
        else:
            await target.message.edit_text(text, reply_markup=kb)
        return

    # Удаляем старые сообщения (только если это CallbackQuery)
    if isinstance(target, CallbackQuery):
        await target.message.delete()

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
        await target.bot.send_message(
            chat_id=target.from_user.id if isinstance(target, Message) else target.message.chat.id,
            text=text,
            reply_markup=kb,
        )

    await target.bot.send_message(
        chat_id=target.from_user.id if isinstance(target, Message) else target.message.chat.id,
        text="↑ Your habits ↑",
        reply_markup=get_refresh_button(),
    )


@router.message(F.text == "My Habits")
async def cmd_my_habits(message: Message, api: APIClient | None):
    if not api:
        await message.answer("Session expired. Please re-authorize using /start")
        return
    await show_habits_list(message, api)


@router.callback_query(F.data == "refresh_habits")
async def cb_refresh_habits(cb: CallbackQuery, api: APIClient | None):
    if not api:
        await cb.answer("Session expired — re-login", show_alert=True)
        return

    await show_habits_list(cb, api)
    await cb.answer()


@router.callback_query(F.data.startswith("complete:"))
async def cb_complete_habit(cb: CallbackQuery, api: APIClient | None):
    if not api:
        await cb.answer("Session expired", show_alert=True)
        return

    habit_id = int(cb.data.split(":")[1])

    try:
        await api.complete_habit(habit_id)
        await cb.answer("Marked as completed!", show_alert=False)
    except HabitAlreadyCompletedError:
        await cb.answer("Already completed today!", show_alert=True)
    except Exception:
        log.exception("Failed to complete habit")
        await cb.answer("Error", show_alert=True)

    await show_habits_list(cb, api)


@router.callback_query(F.data.startswith("delete:"))
async def cb_delete_habit(cb: CallbackQuery, api: APIClient | None):
    if not api:
        await cb.answer("Session expired", show_alert=True)
        return

    habit_id = int(cb.data.split(":")[1])

    try:
        await api.delete_habit(habit_id)
        await cb.answer("Habit deleted", show_alert=False)
    except Exception:
        log.exception("Failed to delete habit")
        await cb.answer("Error deleting", show_alert=True)

    await show_habits_list(cb, api)
