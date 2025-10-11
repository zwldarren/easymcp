"""FastAPI dependencies for the EasyMCP API."""

from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from easymcp.core.database import get_db_session
from easymcp.core.server_manager import ServerManager
from easymcp.models import User
from easymcp.services.auth_service import get_consolidated_auth_service
from easymcp.state import AppState


def get_app_state(request: Request) -> AppState:
    """Get the application state from the request."""
    return request.app.state.app_state


def get_server_manager(state: Annotated[AppState, Depends(get_app_state)]):
    """Get the server manager."""
    if not state.server_manager:
        raise HTTPException(status_code=500, detail="Server manager not initialized")
    return state.server_manager


async def get_db_session_dep() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for FastAPI dependency injection."""
    async with get_db_session() as session:
        yield session


# Type-annotated dependencies for cleaner route signatures
AppStateDep = Annotated[AppState, Depends(get_app_state)]
ServerManagerDep = Annotated[ServerManager, Depends(get_server_manager)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session_dep)]


async def get_api_key_user(
    api_key: str,
    db: DbSessionDep,
    required_scopes: list[str] | None = None,
) -> User:
    """Get user from API key with optional scope validation."""
    auth_service = get_consolidated_auth_service()
    await auth_service.initialize()

    is_valid, user, _ = await auth_service.validate_api_key_for_request(
        db, api_key, required_scopes
    )

    if not is_valid or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or insufficient permissions",
        )

    return user


async def api_key_auth(
    required_scopes: list[str] | None = None,
) -> Callable[[str, DbSessionDep], Awaitable[User]]:
    """Create a dependency for API key authentication."""

    async def dependency(
        api_key: str = Header(..., alias="X-API-Key", description="EasyMCP API Key"),
        db: DbSessionDep = Depends(),  # noqa: B008 - FastAPI Depends is handled by the framework
    ) -> User:
        return await get_api_key_user(api_key, db, required_scopes)

    return dependency


# Additional dependencies for enhanced authentication
async def get_current_user_with_auth_info(request: Request) -> tuple[str, dict]:
    """Dependency to get current user and authentication info from request state."""
    if not hasattr(request.state, "username") or not hasattr(request.state, "auth_info"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return request.state.username, request.state.auth_info


async def require_scope(scope: str, request: Request) -> None:
    """Dependency to require specific scope for the current request."""
    if not hasattr(request.state, "auth_info"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication info not available",
        )

    auth_info = request.state.auth_info
    if auth_info.get("type") == "api_key":
        # Check scopes for API keys
        user_scopes = auth_info.get("scopes", [])
        if scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scope '{scope}' not granted to this API key",
            )
    elif auth_info.get("type") == "jwt":
        # JWT tokens have full access by default
        # You can add additional JWT scope checks here if needed
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication type",
        )


def require_scope_dependency(scope: str):
    """Factory function to create scope requirement dependencies."""

    async def dependency(request: Request):
        return await require_scope(scope, request)

    return dependency
