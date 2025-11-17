"""
Database session configuration.

Provides async SQLAlchemy engine and session factory.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    # Use NullPool for serverless/connection-pooled databases like Neon
    # poolclass=NullPool,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.

    Usage in FastAPI endpoints:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...

    Automatically handles session cleanup and rollback on errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error: %s", str(e), exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection.

    Call this during application startup to verify database connectivity.
    """
    try:
        async with engine.begin() as conn:
            logger.info("Database connection established successfully")
            # Optionally, you can run migrations here or verify tables exist
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e), exc_info=True)
        raise


async def close_db() -> None:
    """
    Close database connection.

    Call this during application shutdown to properly dispose of the engine.
    """
    await engine.dispose()
    logger.info("Database connection closed")
