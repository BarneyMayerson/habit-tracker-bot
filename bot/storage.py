from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "data" / "bot.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


async def init_db() -> None:
    """Initialize SQLite database and create tables if not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_tokens (
                telegram_id INTEGER PRIMARY KEY,
                jwt_token TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def save_user_token(telegram_id: int, jwt_token: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_tokens (telegram_id, jwt_token) VALUES (?, ?)",
            (telegram_id, jwt_token),
        )
        await db.commit()


async def get_user_token(telegram_id: int) -> str | None:
    async with (
        aiosqlite.connect(DB_PATH) as db,
        db.execute("SELECT jwt_token FROM user_tokens WHERE telegram_id = ?", (telegram_id,)) as cursor,
    ):
        row = await cursor.fetchone()
        return row[0] if row else None
