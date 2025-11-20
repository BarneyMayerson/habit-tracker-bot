from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.api.client import APIClient
from bot.storage import save_user_token

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message, bot, api: APIClient | None = None) -> None:
    """Обычный /start или /start auth"""
    # Проверяем, есть ли payload (например, "auth")
    payload = None
    if isinstance(message, Message) and message.text and " " in message.text.strip():
        _, payload = message.text.strip().split(maxsplit=1)

    # Если payload == "auth" — значит пользователь пришёл по deep-link
    if payload == "auth":
        await handle_auth_deep_link(message)
        return

    # Обычный первый запуск
    if api:
        try:
            await api.get_active_habits()
            await message.answer("Welcome back! Use the menu below", reply_markup=main_menu_kb())
            return
        except Exception:  # noqa: S110
            pass

    # Показываем кнопку авторизации
    bot_info = await bot.get_me()
    auth_link = f"https://t.me/{bot_info.username}?start=auth"

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Login with Telegram", url=auth_link)]])

    await message.answer(
        "<b>Habit Tracker</b>\n\nTo get started, please log in using the button below:",
        reply_markup=kb,
    )


async def handle_auth_deep_link(message: Message) -> None:
    """Авторизация по deep-link (локальная dev-версия)"""
    user = message.from_user
    telegram_id = message.from_user.id

    print(f"ID={user.id} | USERNAME={user.username} | FIRST={user.first_name} | LAST={user.last_name}")

    try:
        client = APIClient()
        jwt_token = client.auth_telegram(telegram_id=telegram_id, auth_token="debug_local_auth")
        await save_user_token(telegram_id, jwt_token)

        register_client = APIClient(jwt_token)
        register_client.request(
            "POST",
            "/v1/users/register",
            json={
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        )

        await message.answer(
            "Successfully authorized! ✅\nNow you can track your habits.",
            reply_markup=main_menu_kb(),
        )
    except Exception as e:
        await message.answer(f"Authorization failed: {e}")


def main_menu_kb():
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="My Habits"), KeyboardButton(text="Add Habit")],
            [KeyboardButton(text="Statistics"), KeyboardButton(text="Settings")],
        ],
        resize_keyboard=True,
    )
