from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from bot.api.client import APIClient
from bot.storage import get_user_token


class AuthMiddleware(BaseMiddleware):
    """Inject authenticated APIClient into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user: User = data.get("event_from_user")
        if not telegram_user:
            return await handler(event, data)

        token = await get_user_token(telegram_user.id)
        data["api"] = APIClient(token) if token else None
        data["raw_token"] = token
        return await handler(event, data)
