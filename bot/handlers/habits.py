from aiogram import F, Router
from aiogram.types import Message

from bot.logger import log

router = Router(name="habits")


@router.message(F.text == "My Habits")
async def cmd_my_habits(message: Message):
    """Handle 'My Habits' button press."""
    log.info(f"User {message.from_user.id} requested their habits list")

    await message.answer(
        "Your habits are loading...\nOne moment please",
        reply_markup=None,
    )
