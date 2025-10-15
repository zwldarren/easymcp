"""Database connection and initialization module for PostgreSQL and SQLite."""

import logging
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import inspect
from sqlmodel.ext.asyncio.session import AsyncSession

from easymcp.config import get_settings

logger = logging.getLogger(__name__)

# Global engine and session factory - will be initialized when needed
_engine_lock = threading.Lock()
engine = None
AsyncSessionLocal = None


def _normalize_db_url(raw_url: str) -> str:
    """Normalize database URL for async SQLAlchemy usage.

    If the user provided a plain ``postgresql://`` URL we upgrade it to
    use the asyncpg driver automatically. If it's SQLite without aiosqlite,
    we add the aiosqlite driver.
    """
    # PostgreSQL normalization
    if raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
        new_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return new_url

    # SQLite normalization
    if raw_url.startswith("sqlite://") and "+aiosqlite" not in raw_url:
        new_url = raw_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return new_url

    return raw_url


def get_session_factory():
    """Get the database session factory."""
    global AsyncSessionLocal
    get_db_engine()  # Ensure engine is initialized
    return AsyncSessionLocal


def get_db_engine():
    """Get or create the database engine with connection pooling.

    Provides clearer diagnostics if the appropriate async driver is
    missing and configures connection pooling for production use.
    """
    global engine, AsyncSessionLocal

    if engine is not None:
        return engine

    with _engine_lock:
        if engine is None:
            try:
                settings_obj = get_settings()
                db_url = _normalize_db_url(settings_obj.database_url)

                # Configure connection pooling for better performance
                pool_size = getattr(settings_obj, "db_pool_size", 10)
                max_overflow = getattr(settings_obj, "db_max_overflow", 20)

                # Connection args should be driver-specific
                connect_args = {}
                if "asyncpg" in db_url:
                    connect_args = {
                        "timeout": 30,
                        "command_timeout": 60,
                        "server_settings": {"application_name": "easymcp"},
                    }
                elif "aiosqlite" in db_url:
                    # SQLite specific settings
                    connect_args = {
                        "check_same_thread": False,  # Required for async SQLite
                    }
                elif "postgresql" in db_url and "asyncpg" not in db_url:
                    logger.warning(
                        "Using synchronous PostgreSQL driver with async engine. "
                        "Consider using 'postgresql+asyncpg://' for better performance."
                    )
                elif "sqlite" in db_url and "aiosqlite" not in db_url:
                    logger.warning(
                        "Using synchronous SQLite driver with async engine. "
                        "Consider using 'sqlite+aiosqlite://' for better performance."
                    )

                engine = create_async_engine(
                    db_url,
                    echo=settings_obj.debug,
                    # Connection pool settings
                    pool_size=pool_size,
                    max_overflow=max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    connect_args=connect_args,
                )
                logger.info("Database engine created successfully")

            except ModuleNotFoundError as e:
                logger.error(f"Database driver not found: {str(e)}")
                if "psycopg2" in str(e):
                    logger.error(
                        "PostgreSQL driver 'psycopg2' not installed. Install 'asyncpg' and "
                        "use an async URL, e.g. 'postgresql+asyncpg://user:pass@host/db'."
                    )
                elif "aiosqlite" in str(e) or "sqlite3" in str(e):
                    logger.error(
                        "SQLite driver not found. Install 'aiosqlite' for async SQLite support."
                    )
                raise
            except Exception as e:
                logger.error(f"Error creating database engine: {str(e)}")
                raise

            AsyncSessionLocal = async_sessionmaker(
                bind=engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
            )

    return engine


async def init_db():
    """Initialize the database and run migrations."""
    logger.info("Initializing database...")

    try:
        # Run migrations first
        from easymcp.core.migration import ensure_migrations_run

        await ensure_migrations_run()

        # Get database engine
        db_engine = get_db_engine()

        # Check if User and Session tables exist
        async with db_engine.begin() as conn:
            # Use run_sync to execute the inspection in a synchronous context
            table_names = await conn.run_sync(
                lambda sync_conn: set(inspect(sync_conn).get_table_names())
            )

        if "users" not in table_names:
            raise RuntimeError("Failed to create users table")
        if "sessions" not in table_names:
            raise RuntimeError("Failed to create sessions table")

        # Create default admin user
        from easymcp.services.auth_service import get_consolidated_auth_service

        auth_service = get_consolidated_auth_service()
        async with get_db_session() as session:
            await auth_service.create_default_admin_user(session)

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations.

    This context manager ensures proper session cleanup in all scenarios,
    including exceptions during session creation, commit, rollback, or close.
    """
    session = None
    try:
        # Ensure engine is initialized
        get_db_engine()

        # Check if session factory is available
        if AsyncSessionLocal is None:
            raise RuntimeError("Database session factory not initialized")

        # Create session
        session = AsyncSessionLocal()

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    except Exception:
        raise
    finally:
        if session is not None:
            with suppress(Exception):
                await session.close()
