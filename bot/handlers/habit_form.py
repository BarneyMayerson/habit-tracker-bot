from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api.client import APIClient
from bot.handlers.habits import show_habits_list
from bot.logger import log
from bot.states.habit import HabitForm

router = Router(name="habit_form")


@router.message(F.text == "Add Habit", StateFilter(None))
async def cmd_add_habit(message: Message, state: FSMContext, api: APIClient | None):
    if not api:
        await message.answer("Please authorize first!")
        return

    await state.set_state(HabitForm.waiting_for_title)
    await message.answer(
        "Add new habit\n\nSend me the <b>title</b> of your habit (e.g. 'Run 5 km', 'Read 20 pages')", reply_markup=None
    )


@router.message(HabitForm.waiting_for_title, F.text == "Keep")
async def keep_title(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(title=data["old_habit"]["title"])
    await state.set_state(HabitForm.waiting_for_description)

    await message.answer(
        "Title unchanged.\n\nNow send new description or press Skip / Keep",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Skip")], [types.KeyboardButton(text="Keep")]], resize_keyboard=True
        ),
    )


@router.message(HabitForm.waiting_for_title)
async def process_title(message: Message, state: FSMContext, api: APIClient):
    title = message.text.strip()
    if len(title) < 2:
        await message.answer("Title too short. Try again:")
        return
    if len(title) > 100:
        await message.answer("Title too long (max 100 chars). Try again:")
        return

    await state.update_data(title=title)
    await state.set_state(HabitForm.waiting_for_description)

    data = await state.get_data()
    if "habit_id" in data:
        await message.answer(
            f"New title: <b>{title}</b>\n\nNow send new description or press Skip / Keep",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Skip")], [types.KeyboardButton(text="Keep")]],
                resize_keyboard=True,
            ),
        )
    else:
        await message.answer(
            f"Title: <b>{title}</b>\n\nNow send me a <b>description</b> (optional)\nor press Skip to finish",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Skip")]], resize_keyboard=True, one_time_keyboard=True
            ),
        )


@router.message(HabitForm.waiting_for_description, F.text == "Skip")
async def skip_description(message: Message, state: FSMContext, api: APIClient):
    await process_description(message, state, api, description="")


@router.message(HabitForm.waiting_for_description, F.text.in_({"Skip", "Keep"}))
async def process_edit_description_buttons(message: Message, state: FSMContext, api: APIClient):
    data = await state.get_data()
    old_desc = data["old_habit"].get("description") or ""

    new_desc = old_desc if message.text == "Keep" else ""
    await save_edited_habit(message, state, api, new_desc)


@router.message(HabitForm.waiting_for_description)
async def process_description(message: Message, state: FSMContext, api: APIClient, description: str | None = None):
    if description is None:
        description = message.text.strip()

    if len(description) > 500:
        await message.answer("Description too long (max 500 chars). Try again:")
        return

    data = await state.get_data()
    title = data["title"]

    if "habit_id" in data:
        await save_edited_habit(message, state, api, description)
    else:
        try:
            await api.create_habit(title=title, description=description or None)
            await message.answer(
                f"Habit created!\n\n<b>{title}</b>\n{description or '<i>No description</i>'}",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        except Exception:
            log.exception("Failed to create habit")
            await message.answer("Error creating habit. Try again later.")

        await state.clear()
        await show_habits_list(message, api)


@router.callback_query(F.data.startswith("edit:"))
async def cb_edit_habit(cb: CallbackQuery, state: FSMContext, api: APIClient | None):
    if not api:
        await cb.answer("Session expired", show_alert=True)
        return

    habit_id = int(cb.data.split(":")[1])
    try:
        habit = await api.get_habit(habit_id)
    except Exception:
        await cb.answer("Error loading habit", show_alert=True)
        return

    text = f"Editing habit\n\nCurrent title: <b>{habit['title']}</b>\nSend new title or press Keep to leave unchanged"
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Keep")]], resize_keyboard=True, one_time_keyboard=True
    )

    await cb.message.edit_text(text, reply_markup=None)
    await cb.message.answer("Please continue:", reply_markup=kb)
    await cb.answer()

    await state.update_data(habit_id=habit_id, old_habit=habit)
    await state.set_state(HabitForm.waiting_for_title)


async def save_edited_habit(message: Message, state: FSMContext, api: APIClient, description: str):
    data = await state.get_data()
    habit_id = data["habit_id"]
    title = data["title"]

    try:
        await api.update_habit(habit_id, title=title, description=description or None)
        await message.answer("Habit updated!", reply_markup=types.ReplyKeyboardRemove())
    except Exception:
        await message.answer("Error updating habit")

    await state.clear()
    await show_habits_list(message, api)
