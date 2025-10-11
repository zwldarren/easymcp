"""Unified error handling and logging utilities for EasyMCP."""

import logging
import os
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from easymcp.api.middleware import EasyMCPMiddleware, MiddlewarePriority

logger = logging.getLogger(__name__)


class EasyMCPError(Exception):
    """Base exception class for EasyMCP application."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ServerNotFoundError(EasyMCPError):
    """Raised when a server is not found."""

    def __init__(self, server_name: str):
        super().__init__(
            message=f"Server '{server_name}' not found",
            error_code="SERVER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ServerAlreadyRunningError(EasyMCPError):
    """Raised when trying to start a server that is already running."""

    def __init__(self, server_name: str):
        super().__init__(
            message=f"Server '{server_name}' is already running",
            error_code="SERVER_ALREADY_RUNNING",
            status_code=status.HTTP_409_CONFLICT,
        )


class ServerNotRunningError(EasyMCPError):
    """Raised when trying to stop a server that is not running."""

    def __init__(self, server_name: str):
        super().__init__(
            message=f"Server '{server_name}' is not running",
            error_code="SERVER_NOT_RUNNING",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConfigurationError(EasyMCPError):
    """Raised when there is a configuration error."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def log_error(
    error: Exception, context: dict[str, Any] | None = None, level: int = logging.ERROR
) -> None:
    """Log an error with consistent formatting."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }

    if context:
        error_data.update(context)

    logger.log(level, "Error occurred", extra=error_data)


def create_error_response(error: Exception, request: Request | None = None) -> JSONResponse:
    """Create a consistent error response with production safety."""
    # Determine if we're in production mode
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    # Get detailed error information for logging
    error_type = type(error).__name__
    error_message = str(error)

    # Log the error with full details (always log full error for debugging)
    log_error(
        error,
        {
            "request_path": request.url.path if request else None,
            "error_type": error_type,
            "is_production": is_production,
        },
    )

    if isinstance(error, EasyMCPError):
        status_code = error.status_code
        error_data = {
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details if not is_production else {},
            }
        }
    elif isinstance(error, HTTPException):
        status_code = error.status_code
        error_data = {
            "error": {
                "code": f"HTTP_{error.status_code}",
                "message": error.detail,
                "details": {},
            }
        }
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if is_production:
            # In production, don't expose internal error details
            error_data = {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            }
        else:
            # In development, show detailed error information
            import traceback

            error_data = {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": error_message,
                    "details": {
                        "exception": error_message,
                        "type": error_type,
                        "traceback": traceback.format_exc(),
                    },
                }
            }

    return JSONResponse(
        status_code=status_code,
        content=error_data,
    )


class ErrorHandlingMiddleware(EasyMCPMiddleware):
    """Middleware for unified error handling."""

    @property
    def name(self) -> str:
        return "ErrorHandlingMiddleware"

    def __init__(self, app):
        super().__init__(app, priority=MiddlewarePriority.HIGHEST)

    async def dispatch(self, request: Request, call_next):
        """Handle errors and return a consistent response."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return create_error_response(e, request)


def handle_server_errors(func):
    """Decorator to handle common server-related errors."""

    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # Convert ValueError to appropriate EasyMCPError
            error_msg = str(e).lower()
            if "not found" in error_msg:
                raise ServerNotFoundError(str(e)) from e
            elif "already running" in error_msg:
                raise ServerAlreadyRunningError(str(e)) from e
            elif "not running" in error_msg:
                raise ServerNotRunningError(str(e)) from e
            elif "not initialized" in error_msg:
                raise ConfigurationError(str(e)) from e
            else:
                raise ConfigurationError(str(e)) from e

    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # Convert ValueError to appropriate EasyMCPError
            error_msg = str(e).lower()
            if "not found" in error_msg:
                raise ServerNotFoundError(str(e)) from e
            elif "already running" in error_msg:
                raise ServerAlreadyRunningError(str(e)) from e
            elif "not running" in error_msg:
                raise ServerNotRunningError(str(e)) from e
            elif "not initialized" in error_msg:
                raise ConfigurationError(str(e)) from e
            else:
                raise ConfigurationError(str(e)) from e

    # Check if the function is async
    import inspect

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
