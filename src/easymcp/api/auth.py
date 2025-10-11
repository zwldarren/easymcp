"""Authentication middleware for JWT and API key validation."""

import logging
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, Request, Response, status
from starlette.responses import JSONResponse

from easymcp.config import get_settings
from easymcp.core.database import get_db_session
from easymcp.services.auth_service import get_consolidated_auth_service

from .middleware import EasyMCPMiddleware, MiddlewareContext, MiddlewarePriority

logger = logging.getLogger(__name__)


@dataclass
class AuthenticationResult:
    """Result of authentication attempt."""

    is_valid: bool
    username: str | None = None
    auth_info: dict | None = None
    error: Exception | None = None
    error_message: str | None = None


class AuthenticationError(Exception):
    """Base authentication error."""

    def __init__(self, message: str, error_code: str = "AUTHENTICATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid or expired."""

    def __init__(self, message: str = "Invalid or expired credentials."):
        super().__init__(message, "INVALID_CREDENTIALS")


class InvalidAuthenticationSchemeError(AuthenticationError):
    """Raised when authentication scheme is invalid."""

    def __init__(self, message: str = "Invalid authentication scheme."):
        super().__init__(message, "INVALID_AUTH_SCHEME")


class InvalidAuthenticationHeaderError(AuthenticationError):
    """Raised when authentication header format is invalid."""

    def __init__(self, message: str = "Invalid authentication header format."):
        super().__init__(message, "INVALID_AUTH_HEADER")


class AuthMiddleware(EasyMCPMiddleware):
    """Authentication middleware for JWT and API key validation."""

    @property
    def name(self) -> str:
        return "AuthMiddleware"

    def __init__(self, app):
        super().__init__(app, priority=MiddlewarePriority.AUTHENTICATION)
        self.auth_service = get_consolidated_auth_service()
        self.settings = get_settings()

    def _is_public_path(self, request: Request) -> bool:
        """Check if the request path is public."""
        # Public paths that do not require authentication
        public_paths = [
            "/",
            "/health",
            "/api/auth/login",
            "/api/auth/api-keys",
            "/login",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/register",
        ]

        # Public path prefixes that do not require authentication
        public_path_prefixes = [
            "/_next",
            "/app",
            "/docs",
            "/.well-known",
        ]

        # Check if the request path is public
        is_public = request.url.path in public_paths or any(
            request.url.path.startswith(prefix) for prefix in public_path_prefixes
        )

        if request.method == "OPTIONS":
            if request.url.path.startswith("/api/"):
                return True
            if any(request.url.path.startswith(prefix) for prefix in public_path_prefixes):
                return True

        return is_public

    def _is_mcp_server_endpoint(self, request: Request) -> bool:
        """Check if the request is for a MCP server endpoint."""
        return request.url.path.startswith("/servers/") and "/mcp" in request.url.path

    def _get_required_scopes(self, request: Request) -> list[str]:
        """Get the required scopes for the requested endpoint."""
        # MCP server endpoints require specific scopes
        if self._is_mcp_server_endpoint(request):
            if request.method in ["GET", "HEAD"]:
                return ["read:servers"]
            else:
                return ["access:servers"]

        # Default to read:servers for most server operations
        if request.url.path.startswith("/servers/"):
            if request.method in ["GET", "HEAD"]:
                return ["read:servers"]
            else:
                return ["read:servers"]

        # Default minimal scope for authenticated endpoints
        return []

    async def _validate_jwt_token(self, token: str) -> tuple[str | None, Literal["jwt"] | None]:
        """Validate JWT token and return username if valid."""
        username = self.auth_service.verify_token(token)
        return username, "jwt" if username else None

    async def _validate_api_key(
        self, tokens: list[str], required_scopes: list[str]
    ) -> tuple[str | None, dict | None]:
        """Validate API key and return user info if valid."""
        for token in tokens:
            try:
                async with get_db_session() as db:
                    (
                        is_valid,
                        user,
                        api_key_record,
                    ) = await self.auth_service.validate_api_key_for_request(
                        db, token, required_scopes
                    )
                    if is_valid and user and api_key_record:
                        return user.username, {
                            "type": "api_key",
                            "scopes": api_key_record.scopes,
                            "user_id": user.id,
                            "api_key_record": api_key_record,
                        }
            except Exception:
                continue
        return None, None

    async def _authenticate_request(
        self, request: Request, auth_header: str | None, api_key_header: str | None
    ) -> AuthenticationResult:
        """Authenticate request using either JWT or API key."""
        required_scopes = self._get_required_scopes(request)

        # Try API key authentication first (from x-api-key header)
        if api_key_header:
            username, auth_info = await self._validate_api_key([api_key_header], required_scopes)
            if username and auth_info:
                return AuthenticationResult(is_valid=True, username=username, auth_info=auth_info)
            else:
                logger.warning(
                    f"API key validation failed for key starting with: {api_key_header[:8]}_..."
                )

        # Try JWT authentication (from Authorization header)
        if auth_header:
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    return AuthenticationResult(
                        is_valid=False,
                        error=InvalidAuthenticationSchemeError(),
                        error_message="Invalid authentication scheme.",
                    )
            except ValueError:
                return AuthenticationResult(
                    is_valid=False,
                    error=InvalidAuthenticationHeaderError(),
                    error_message="Invalid authentication header format.",
                )

            username, auth_type = await self._validate_jwt_token(token)
            if username:
                return AuthenticationResult(
                    is_valid=True, username=username, auth_info={"type": "jwt"}
                )

        return AuthenticationResult(
            is_valid=False,
            error=InvalidCredentialsError(),
            error_message="Invalid or expired credentials.",
        )

    async def pre_process(self, request: Request, context: MiddlewareContext) -> Response | None:
        """Handle authentication before the request is processed."""
        # Skip authentication if disabled
        if not self.settings.auth_enabled:
            return None

        # Check if the request path is public
        if self._is_public_path(request):
            return None

        # Extract tokens from headers
        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("x-api-key")

        # Must have at least one authentication header
        if not auth_header and not api_key_header:
            logger.warning(
                f"No Authorization or x-api-key header found for path: {request.url.path}"
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication credentials were not provided."},
            )

        # Authenticate request
        auth_result = await self._authenticate_request(request, auth_header, api_key_header)
        if not auth_result.is_valid:
            # Handle authentication errors
            path = request.url.path
            error_msg = f"Authentication failed for path: {path} - {auth_result.error_message}"
            logger.warning(error_msg)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": auth_result.error_message},
            )

        # Add user info to request state and context
        request.state.username = auth_result.username
        request.state.auth_info = auth_result.auth_info

        # Update middleware context
        context.username = auth_result.username
        context.auth_type = auth_result.auth_info.get("type") if auth_result.auth_info else None

        if auth_result.auth_info and "scopes" in auth_result.auth_info:
            context.auth_scopes = auth_result.auth_info["scopes"]

        # Log authentication success
        if auth_result.auth_info:
            logger.info(
                f"Authentication successful for {auth_result.username} via "
                f"{auth_result.auth_info.get('type', 'unknown')} on path: {request.url.path}"
            )
        else:
            path = request.url.path
            success_msg = f"Authentication successful for {auth_result.username} on path: {path}"
            logger.info(success_msg)

        return None


async def get_current_user(request: Request) -> str:
    """Dependency to get current user from request state."""
    if not hasattr(request.state, "username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return request.state.username


async def get_current_token(request: Request) -> str:
    """Dependency to get current token from request state."""
    if not hasattr(request.state, "token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found",
        )
    return request.state.token
