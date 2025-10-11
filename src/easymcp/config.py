"""Unified configuration management for EasyMCP."""

import logging
import os
import sys

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str = Field(
        default="sqlite:///./easymcp.sqlite",
        description=(
            "Database connection URL. Use 'sqlite:///path/to/database.db' for SQLite "
            "or 'postgresql://...' for PostgreSQL"
        ),
    )

    # Server
    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8000, description="Server port number")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Application
    pass_environment: bool = Field(default=False, description="Pass environment to MCP servers")
    allowed_origins: list[str] = Field(
        default=["*"],
        description="Comma-separated list of allowed CORS origins. Use ['*'] for all.",
    )

    # Database connection pool settings
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Database connection pool max overflow")

    # Authentication Settings
    auth_enabled: bool = Field(default=True, description="Enable authentication")
    jwt_secret_key: str = Field(default="changeme-in-production", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(
        default=1440, description="JWT expiration in minutes (24 hours)"
    )

    # First-run admin user settings
    admin_username: str = Field(default="admin", description="Default admin username")
    admin_password: str = Field(default="changeme123", description="Default admin password")
    admin_email: str = Field(default="admin@example.com", description="Default admin email")

    class Config:
        env_file = ".env"
        env_prefix = "EASYMCP_"
        case_sensitive = False


def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None:
    """
    Set up the root logger with a handler that outputs to stderr and optionally to a file.
    """
    # Validate log level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid log level: {log_level}. Must be one of: {', '.join(valid_levels)}"
        )

    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Add a file handler if a log file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the singleton settings instance.

    The default database URL uses the asyncpg driver. If an environment
    variable provides a plain ``postgresql://`` URL the database module
    will transparently upgrade it to ``postgresql+asyncpg://`` and log a
    warning.
    """
    global settings
    if settings is None:
        settings = Settings()
    return settings
