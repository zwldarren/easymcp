"""Authentication API router."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from easymcp.api.dependencies import DbSessionDep
from easymcp.models import (
    APIKeyCreatedResponse,
    APIKeyCreateRequest,
    APIKeyListResponse,
    APIKeyResponse,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    ScopeListResponse,
    User,
    UserResponse,
)
from easymcp.services.auth_service import get_consolidated_auth_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: DbSessionDep,
):
    """Authenticate user and create session."""

    try:
        auth_service = get_consolidated_auth_service()
        await auth_service.initialize()

        # Authenticate user
        user = await auth_service.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # Create session
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        session = await auth_service.create_session(db, user, user_agent, ip_address)

        # Update last login
        user.last_login = datetime.now(UTC).replace(tzinfo=None)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        assert user.id is not None, "User ID should not be None after creation"

        return LoginResponse(
            access_token=session.session_token,
            expires_in=auth_service.settings.jwt_expiration_minutes * 60,
            user=UserResponse(id=user.id, username=user.username, email=user.email),
        )
    except HTTPException:
        # Re-raise HTTP exceptions as they are intended responses
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login",
        ) from e


@router.post("/logout")
async def logout(
    request: Request,
    db: DbSessionDep,
):
    """Invalidate current session."""
    if not hasattr(request.state, "username") or not hasattr(request.state, "auth_info"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    auth_service = get_consolidated_auth_service()
    await auth_service.initialize()

    # Get the token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No authorization header"
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header"
        ) from e

    # Delete session
    await auth_service.delete_session(db, token)

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    db: DbSessionDep,
):
    """Get current user information."""
    if not hasattr(request.state, "username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    username = request.state.username

    result = await db.exec(select(User).where(User.username == username))
    user = result.one_or_none()

    if not user or user.id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return UserResponse(id=user.id, username=user.username, email=user.email)


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    db: DbSessionDep,
):
    """Change user password."""
    if not hasattr(request.state, "username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    username = request.state.username

    auth_service = get_consolidated_auth_service()
    await auth_service.initialize()
    # Get user
    result = await db.exec(select(User).where(User.username == username))
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Verify current password
    if not auth_service.verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Update password
    user.password_hash = auth_service.get_password_hash(password_data.new_password)
    user.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.add(user)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    api_key_data: APIKeyCreateRequest,
    request: Request,
    db: DbSessionDep,
):
    """Create a new API key for the authenticated user."""
    # Check if user is authenticated via JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    # Extract token from header
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme"
            )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format"
        ) from err

    # Validate the JWT token
    auth_service = get_consolidated_auth_service()
    await auth_service.initialize()
    username = auth_service.verify_token(token)

    # Get user by username
    result = await db.exec(select(User).where(User.username == username))
    user = result.one_or_none()

    if not user or not user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    try:
        # Create API key with default scopes
        api_key_record, api_key = await auth_service.create_api_key(
            db,
            user.id,
            api_key_data.name,
            None,  # Use default scopes
            api_key_data.description,
        )

        # Ensure API key ID is not None
        if api_key_record.id is None:
            raise ValueError("API key creation failed - ID is None")

        return APIKeyCreatedResponse(
            id=api_key_record.id,
            name=api_key_record.name,
            api_key=api_key,
            key_prefix=api_key_record.key_prefix,
            scopes=api_key_record.scopes,
            created_at=api_key_record.created_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the API key",
        ) from e


@router.get("/api-keys", response_model=APIKeyListResponse)
async def get_user_api_keys(
    request: Request,
    db: DbSessionDep,
):
    """Get all API keys for the authenticated user."""
    # Check if user is authenticated via JWT token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    # Extract token from header
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme"
            )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format"
        ) from err

    # Validate the JWT token
    auth_service = get_consolidated_auth_service()
    await auth_service.initialize()
    username = auth_service.verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    result = await db.exec(select(User).where(User.username == username))
    user = result.one_or_none()

    if not user or not user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    try:
        # Get API keys
        api_keys = await auth_service.get_user_api_keys(db, user.id)

        # Convert to API response format
        api_key_responses = [
            APIKeyResponse(
                id=api_key.id,
                name=api_key.name,
                description=api_key.description,
                key_prefix=api_key.key_prefix,
                key_hash=api_key.key_hash,
                scopes=api_key.scopes,
                is_active=api_key.is_active,
                created_at=api_key.created_at,
                last_used=api_key.last_used,
            )
            for api_key in api_keys
            if api_key.id is not None
        ]

        return APIKeyListResponse(api_keys=api_key_responses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching API keys",
        ) from e


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    request: Request,
    db: DbSessionDep,
):
    """Delete an API key permanently for the authenticated user."""
    if not hasattr(request.state, "username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    username = request.state.username

    result = await db.exec(select(User).where(User.username == username))
    user = result.one_or_none()

    auth_service = get_consolidated_auth_service()
    await auth_service.initialize()
    if not user or not user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    try:
        # Delete API key
        success = await auth_service.delete_api_key(db, key_id, user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found",
            )

        return {"message": "API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the API key",
        ) from e


@router.get("/api-keys/scopes", response_model=ScopeListResponse)
async def get_available_scopes():
    """Get available API key scopes and their descriptions."""
    return ScopeListResponse()
