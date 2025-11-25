from aiogram.fsm.state import State, StatesGroup


class HabitForm(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
