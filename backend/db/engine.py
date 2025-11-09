"""
Database engine configuration.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.core.config import settings


def get_engine() -> AsyncEngine:
    """Create and return async engine."""
    return create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        future=True,
    )
