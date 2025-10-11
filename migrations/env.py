import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from sqlmodel import SQLModel

target_metadata = SQLModel.metadata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from easymcp.models import *  # noqa: F403,F401,E402

config = context.config


def get_url() -> str:
    import os

    return os.getenv("EASYMCP_DATABASE_URL", "sqlite:///./easymcp.sqlite")


config.set_main_option("sqlalchemy.url", get_url())

fileConfig(config.config_file_name)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
