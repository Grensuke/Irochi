"""
Async SQLAlchemy engine and session factory.
Connects to PostgreSQL on localhost via asyncpg.

Production-hardened connection pool settings.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,       # Test connection before use
    pool_recycle=3600,         # Recycle stale connections after 1 hour
    echo=False,               # Set True only for SQL debugging
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass
