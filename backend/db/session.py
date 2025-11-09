"""
Async database session factory.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.db.engine import get_engine

engine = get_engine()
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
