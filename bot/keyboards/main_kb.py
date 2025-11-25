from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="My Habits"), KeyboardButton(text="Add Habit")],
            [KeyboardButton(text="Statistics"), KeyboardButton(text="Settings")],
        ],
        resize_keyboard=True,
    )
