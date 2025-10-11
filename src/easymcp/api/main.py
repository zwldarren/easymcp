"""Main FastAPI application for the EasyMCP API."""

import logging
import os
import re
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, Response

from easymcp.config import get_settings
from easymcp.lifespan import lifespan
from easymcp.state import app_state

from ..core.errors import ErrorHandlingMiddleware
from .auth import AuthMiddleware
from .middleware import (
    ActivityTrackerMiddleware,
    MetricsTrackerMiddleware,
    MiddlewareManager,
    SecurityHeadersMiddleware,
)
from .routers import auth, config, servers, status

logger = logging.getLogger(__name__)


def _is_valid_path(path: str) -> bool:
    """Validate that the path is safe and doesn't contain path traversal attempts.

    Args:
        path: The path string to validate

    Returns:
        True if the path is safe, False otherwise
    """
    if not isinstance(path, str):
        return False

    # Decode URL-encoded characters
    try:
        decoded_path = unquote(path)
    except Exception:
        return False

    # Check for common path traversal patterns
    traversal_patterns = [
        r"\.\.",  # Directory traversal
        r"//",  # Double slashes
        r"\\",  # Backslashes (Windows paths)
        r"~",  # Home directory reference
        r"^/",  # Absolute paths
        r"^\w+:",  # Windows drive letters
    ]

    for pattern in traversal_patterns:
        if re.search(pattern, decoded_path):
            return False

    # Check for control characters
    if any(ord(c) < 32 for c in decoded_path):
        return False

    # Check for null bytes
    return "\x00" not in decoded_path


def _sanitize_path(path: str) -> str:
    """Sanitize the path by removing dangerous characters and normalizing.

    Args:
        path: The path to sanitize

    Returns:
        A sanitized and normalized path
    """
    # Decode URL-encoded characters
    decoded_path = unquote(path)

    # Normalize the path
    normalized_path = os.path.normpath(decoded_path)

    # Remove any leading slashes or dots
    sanitized_path = normalized_path.lstrip("/").lstrip(".")

    # Remove any trailing slashes
    sanitized_path = sanitized_path.rstrip("/")

    return sanitized_path


def _construct_and_validate_path(base_dir: str, relative_path: str) -> Path:
    """Construct and validate the full path to ensure it's within the base directory.

    Args:
        base_dir: The base directory path
        relative_path: The relative path to validate

    Returns:
        A validated Path object representing the safe path

    Raises:
        ValueError: If the path is invalid or attempts to escape the base directory
    """
    # Convert to absolute paths
    base_dir_path = Path(base_dir).resolve()
    relative_path_path = Path(relative_path)

    # Construct the full path
    full_path = (base_dir_path / relative_path_path).resolve()

    # Verify that the resolved path is within the base directory
    if not full_path.is_relative_to(base_dir_path):
        raise ValueError(f"Path traversal attempt detected: {relative_path}")

    return full_path


app = FastAPI(lifespan=lifespan)

# Attach the application state to the app instance
app.state.app_state = app_state

# Initialize middleware manager
middleware_manager = MiddlewareManager(app)

# Add middleware using the manager for better organization and future extensibility
settings_obj = get_settings()

# Register middleware with their configurations
middleware_manager.register_middleware(
    CORSMiddleware,
    allow_origins=settings_obj.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
middleware_manager.register_middleware(SecurityHeadersMiddleware)
middleware_manager.register_middleware(ErrorHandlingMiddleware)
middleware_manager.register_middleware(MetricsTrackerMiddleware)
middleware_manager.register_middleware(ActivityTrackerMiddleware)
middleware_manager.register_middleware(AuthMiddleware)

# Setup the middleware chain in the correct order
middleware_manager.setup_middleware_chain()


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(servers.router, prefix="/api/servers", tags=["servers"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(status.router, prefix="/api/status", tags=["status"])


@app.get(
    "/health",
    response_model=dict[str, str],
    summary="Health check",
    description="Simple health check endpoint to verify the API is running.",
    responses={200: {"description": "API is healthy"}, 503: {"description": "API is unhealthy"}},
)
async def health_check() -> dict[str, str]:
    """A simple health check endpoint."""
    return {"status": "ok"}


@app.get(
    "/",
    summary="Serve frontend root",
    description="Serves the frontend application's root page.",
    include_in_schema=False,  # Exclude from OpenAPI schema as it's a frontend route
)
async def serve_frontend_root():
    """Serve the frontend application for root path."""
    try:
        # Validate the index path is safe
        index_path = _construct_and_validate_path(STATIC_DIR, "index.html")

        # Check if the file actually exists
        if not index_path.exists() or not index_path.is_file():
            return Response("Frontend not available", status_code=503)

        return FileResponse(str(index_path))
    except ValueError:
        return Response("Frontend not available", status_code=503)
    except PermissionError:
        return Response("Frontend access denied", status_code=403)
    except Exception:
        return Response("Internal server error", status_code=500)


STATIC_DIR = "frontend/out"

# Mount the Next.js static assets directory under /
app.mount(
    "/_next",
    StaticFiles(directory=os.path.join(STATIC_DIR, "_next")),
    name="next-static",
)


# Catch-all route to serve the frontend under / (excluding root and API routes)
@app.get(
    "/{full_path:path}",
    include_in_schema=False,  # Exclude from OpenAPI schema as it's a frontend route
)
async def serve_frontend(request: Request):
    """Serves the frontend application under / path."""
    path = request.path_params.get("full_path", "")

    # Skip API and server routes
    if path.startswith("api/") or path.startswith("servers/"):
        return Response("Not Found", status_code=404)

    # Skip root path (already handled by serve_frontend_root)
    if path == "" or path == "/":
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    # Validate path before any processing
    try:
        # Validate input path is safe
        if not _is_valid_path(path):
            return Response("Invalid path", status_code=400)

        # Normalize and sanitize the path
        sanitized_path = _sanitize_path(path)

        # Construct and validate the full path
        static_file_path = _construct_and_validate_path(STATIC_DIR, sanitized_path)

    except Exception:
        return Response("Invalid path", status_code=400)

    try:
        # Handle directory requests by serving index.html
        if static_file_path.is_dir():
            index_path = static_file_path / "index.html"
            if index_path.exists() and index_path.is_file():
                return FileResponse(str(index_path))

        # Serve the file if it exists and is a regular file
        if static_file_path.exists() and static_file_path.is_file():
            return FileResponse(str(static_file_path))

        # For client-side routing, always return index.html
        index_path = Path(STATIC_DIR) / "index.html"
        if index_path.exists() and index_path.is_file():
            return FileResponse(str(index_path))
        else:
            return Response("Frontend not available", status_code=503)

    except PermissionError:
        return Response("Access denied", status_code=403)
    except Exception:
        return Response("Internal server error", status_code=500)
