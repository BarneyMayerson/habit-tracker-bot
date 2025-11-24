from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_habit_buttons(habit_id: int, completed_today: bool = False) -> InlineKeyboardMarkup:
    """Buttons below the habit."""
    builder = InlineKeyboardBuilder()

    complete_text = "Completed" if completed_today else "Complete"
    builder.row(
        InlineKeyboardButton(text=complete_text, callback_data=f"complete:{habit_id}"),
        InlineKeyboardButton(text="Edit", callback_data=f"edit:{habit_id}"),
        InlineKeyboardButton(text="Delete", callback_data=f"delete:{habit_id}"),
    )
    return builder.as_markup()


def get_refresh_button() -> InlineKeyboardMarkup:
    """Refresh habit list button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Refresh", callback_data="refresh_habits")
    return builder.as_markup()
