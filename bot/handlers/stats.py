from aiogram import F, Router
from aiogram.types import Message

from bot.api.client import APIClient
from bot.decorators.auth import auth_required
from bot.logger import log

router = Router(name="stats")


@router.message(F.text == "Statistics")
@auth_required
async def cmd_statistics(message: Message, api: APIClient):
    log.info(f"User {message.from_user.id} requested statistics")

    try:
        stats = await api.request("GET", "/v1/habits/stats")
    except Exception:
        log.exception("Failed to fetch stats")
        await message.answer("Error loading statistics")
        return

    s = stats

    fire = "Fire" * min(s["current_streak_days"], 10)
    if s["current_streak_days"] > 10:
        fire += f" +{s['current_streak_days'] - 10}"

    lines = [
        "<b>Your Habit Statistics</b>\n",
        f"Active habits: <b>{s['total_active_habits']}</b>",
        f"Completed today: <b>{s['completed_today']}</b>",
        f"This week: <b>{s['completed_this_week']}</b>",
        f"All time: <b>{s['total_completions_all_time']}</b>",
        "",
        f"Current streak: <b>{s['current_streak_days']} day{'s' if s['current_streak_days'] != 1 else ''}</b>",
        f"{fire}",
    ]

    if s["best_habit"]:
        lines.append(f"\nBest habit: <b>{s['best_habit']}</b> ({s['best_habit_count']} times)")

    await message.answer("\n".join(lines))
