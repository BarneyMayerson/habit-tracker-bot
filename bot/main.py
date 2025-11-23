import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.handlers import habits, start
from bot.logger import log
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.storage import init_db

settings = get_settings()
logging.basicConfig(level=logging.CRITICAL)


async def on_startup(bot: Bot) -> None:
    await init_db()
    log.info("Bot started.")


async def on_shutdown(bot: Bot):
    log.info("Bot shutting down...")


async def main() -> None:
    bot = Bot(token=settings.telegram_bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(AuthMiddleware())
    dp.include_router(start.router)
    dp.include_router(habits.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    log.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
