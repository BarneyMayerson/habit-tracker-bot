import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings

# Импортируем хендлеры
from bot.handlers import start
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.storage import init_db

settings = get_settings()
logging.basicConfig(level=logging.INFO)


async def on_startup(bot: Bot) -> None:
    await init_db()
    logging.info("Bot started")


async def main() -> None:
    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middleware
    dp.update.middleware(AuthMiddleware())

    # Роутеры
    dp.include_router(start.router)
    # dp.include_router(habits.router)
    # dp.include_router(common.router)

    dp.startup.register(on_startup)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
