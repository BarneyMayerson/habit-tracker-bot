from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base
from backend.models.timestamp_mixin import TimestampMixin


class User(Base, TimestampMixin):
    """
    User model.
    Represents a Telegram user in the system.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
