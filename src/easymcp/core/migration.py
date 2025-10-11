"""Database migration management module."""

import logging
import os

from alembic import command
from alembic.config import Config

from easymcp.config import get_settings

logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    """Get Alembic configuration with proper database URL."""
    settings = get_settings()

    # Get the project root directory (where alembic.ini is located)
    current_file = os.path.abspath(__file__)
    # src/easymcp/core/migration.py -> project root (need to go up 4 levels)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))

    # Create Alembic config from the alembic.ini file
    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)

    # Override the database URL
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    # Set script location explicitly
    migrations_path = os.path.join(project_root, "migrations")
    alembic_cfg.set_main_option("script_location", migrations_path)

    return alembic_cfg


def run_migrations() -> None:
    """Run database migrations to the latest version."""
    try:
        alembic_cfg = get_alembic_config()
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running database migrations: {e}")
        raise


def check_migration_status() -> dict[str, str]:
    """Check current migration status."""
    try:
        get_alembic_config()

        # Get current revision from database directly
        import asyncio

        from sqlalchemy import inspect, text

        from easymcp.core.database import get_db_engine

        async def get_current_version():
            engine = get_db_engine()
            async with engine.begin() as conn:
                # Check if alembic_version table exists
                table_names = await conn.run_sync(
                    lambda sync_conn: inspect(sync_conn).get_table_names()
                )

                if "alembic_version" in table_names:
                    # Get the current version from the table
                    result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                    row = result.fetchone()
                    return row[0] if row else None
            return None

        try:
            # Check if we're already in an event loop
            try:
                asyncio.get_running_loop()
                # If we're in a loop, create a task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_current_version())
                    current = future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                current = asyncio.run(get_current_version())
        except Exception as e:
            logger.warning(f"Could not get current version from database: {e}")
            current = None

        # Get latest revision by checking migration files
        import os
        import re

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        versions_dir = os.path.join(project_root, "migrations", "versions")

        latest = None
        if os.path.exists(versions_dir):
            migration_files = [
                f for f in os.listdir(versions_dir) if f.endswith(".py") and f != "__init__.py"
            ]
            if migration_files:
                # Extract revision IDs from filenames
                revisions = []
                for f in migration_files:
                    match = re.match(r"([a-f0-9]+)_", f)
                    if match:
                        revisions.append(match.group(1))
                if revisions:
                    latest = sorted(revisions)[-1]  # Get the highest revision

        return {
            "current": current or "None (no migrations applied)",
            "latest": latest or "None (no migrations available)",
            "needs_upgrade": current != latest,
        }
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return {"current": "Error", "latest": "Error", "needs_upgrade": False, "error": str(e)}


def create_migration(message: str) -> str:
    """Create a new migration."""
    try:
        alembic_cfg = get_alembic_config()
        logger.info(f"Creating migration: {message}")

        # Generate migration
        revision = command.revision(alembic_cfg, autogenerate=True, message=message)

        logger.info(f"Migration created: {revision.revision}")
        return revision.revision
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        raise


def downgrade_migration(revision: str) -> None:
    """Downgrade to a specific revision."""
    try:
        alembic_cfg = get_alembic_config()
        logger.info(f"Downgrading to revision: {revision}")
        command.downgrade(alembic_cfg, revision)
        logger.info("Database downgrade completed successfully")
    except Exception as e:
        logger.error(f"Error downgrading database: {e}")
        raise


def get_migration_history() -> list[dict[str, str]]:
    """Get migration history."""
    try:
        # Get migration history by reading files directly
        import os
        import re

        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        versions_dir = os.path.join(project_root, "migrations", "versions")

        migrations = []
        if os.path.exists(versions_dir):
            migration_files = [
                f for f in os.listdir(versions_dir) if f.endswith(".py") and f != "__init__.py"
            ]
            migration_files.sort()  # Sort by filename (chronological order)

            for f in migration_files:
                # Extract revision ID from filename
                match = re.match(r"([a-f0-9]+)_(.+)\.py", f)
                if match:
                    revision = match.group(1)
                    description = match.group(2).replace("_", " ").title()

                    # Read the file to get more details
                    file_path = os.path.join(versions_dir, f)
                    try:
                        with open(file_path, encoding="utf-8") as file:
                            content = file.read()
                            # Extract down_revision
                            down_match = re.search(
                                r'down_revision\s*=\s*[\'"]([^\'\"]+)[\'"]', content
                            )
                            down_revision = down_match.group(1) if down_match else None

                            # Extract docstring
                            doc_match = re.search(r'"""([^"]+)"""', content)
                            doc = doc_match.group(1) if doc_match else description
                    except Exception:
                        down_revision = None
                        doc = description

                    migrations.append(
                        {
                            "revision": revision,
                            "down_revision": down_revision,
                            "branch_labels": None,
                            "depends_on": None,
                            "doc": doc,
                        }
                    )

        return migrations
    except Exception as e:
        logger.error(f"Error getting migration history: {e}")
        return []


async def ensure_migrations_run() -> None:
    """Ensure migrations are run before application startup."""
    try:
        status = check_migration_status()

        if status.get("error"):
            logger.warning(f"Could not check migration status: {status['error']}")
            return

        if status["needs_upgrade"]:
            logger.info("Database migrations are needed, running them now...")
            run_migrations()
        else:
            logger.info("Database is up to date")

    except Exception as e:
        logger.error(f"Error ensuring migrations are run: {e}")
