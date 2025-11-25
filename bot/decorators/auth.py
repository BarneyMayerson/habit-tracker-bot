from collections.abc import Callable
from functools import wraps

from aiogram.types import CallbackQuery, Message


def auth_required(handler: Callable) -> Callable:
    @wraps(handler)
    async def wrapper(message_or_callback: Message | CallbackQuery, *args, **kwargs):
        api = kwargs.get("api")

        if not api:
            if isinstance(message_or_callback, Message):
                await message_or_callback.answer("Please authorize first!")
            else:  # CallbackQuery
                await message_or_callback.answer("Please authorize first!", show_alert=True)
            return None

        return await handler(message_or_callback, *args, **kwargs)

    return wrapper
