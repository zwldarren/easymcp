"""Consolidated authentication service combining core and services functionality."""

import logging
import secrets
import string
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from easymcp.config import get_settings
from easymcp.core.database import get_db_session
from easymcp.models import (
    APIKey,
    APIKeyCreateRequest,
    APIKeyResponse,
    ApiKeyScope,
    LoginRequest,
    LoginResponse,
    Session,
    User,
    UserResponse,
)

logger = logging.getLogger(__name__)


class ConsolidatedAuthService:
    """Consolidated authentication service handling all auth operations."""

    def __init__(self):
        self.settings = get_settings()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the authentication service."""
        if self._initialized:
            return
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    # Password Methods
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            if not plain_password or not hashed_password:
                return False
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except (ValueError, Exception):
            return False

    def get_password_hash(self, password: str) -> str:
        """Create a password hash."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # JWT Methods
    def create_access_token(self, username: str) -> str:
        """Create a JWT access token."""
        if not self.settings.jwt_secret_key:
            raise ValueError("JWT secret key is not configured")
        if not self.settings.jwt_algorithm:
            raise ValueError("JWT algorithm is not configured")

        expires_delta = timedelta(minutes=self.settings.jwt_expiration_minutes)
        expire = datetime.now(UTC) + expires_delta
        to_encode = {"sub": username, "exp": expire}

        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )
        return encoded_jwt

    def verify_token(self, token: str) -> str | None:
        """Verify a JWT token and return username if valid."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            username = payload.get("sub")
            return username
        except JWTError:
            return None

    # User Authentication Methods
    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str
    ) -> User | None:
        """Authenticate a user with username and password."""
        try:
            result = await db.execute(
                select(User).where(col(User.username) == username, col(User.is_active))
            )
            user = result.scalar_one_or_none()

            if not user or not self.verify_password(password, user.password_hash):
                return None

            return user
        except Exception:
            return None

    async def create_session(
        self,
        db: AsyncSession,
        user: User,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> Session:
        """Create a new session for a user."""
        if not user.id:
            raise ValueError("User ID is required to create session")

        token = self.create_access_token(user.username)
        expires_at = (
            datetime.now(UTC) + timedelta(minutes=self.settings.jwt_expiration_minutes)
        ).replace(tzinfo=None)

        session = Session(
            user_id=user.id,
            session_token=token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    async def validate_session(self, db: AsyncSession, token: str) -> bool:
        """Validate a session token."""
        username = self.verify_token(token)
        if not username:
            return False

        result = await db.execute(
            select(Session).where(
                col(Session.session_token) == token,
                col(Session.expires_at) > datetime.now(UTC).replace(tzinfo=None),
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return False

        session.last_accessed_at = datetime.now(UTC).replace(tzinfo=None)
        await db.commit()
        return True

    async def delete_session(self, db: AsyncSession, token: str) -> bool:
        """Delete a session by token."""
        result = await db.execute(select(Session).where(col(Session.session_token) == token))
        session = result.scalar_one_or_none()

        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False

    # High-level User Methods (from services layer)
    async def login(self, request: LoginRequest) -> LoginResponse:
        """Authenticate a user and create a session."""
        if not self._initialized:
            await self.initialize()

        async with get_db_session() as session:
            user = await self.authenticate_user(session, request.username, request.password)
            if not user:
                raise ValueError("Invalid credentials")

            access_token = self.create_access_token(user.username)
            await self.create_session(session, user)

            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=86400,  # 24 hours
                user=UserResponse(
                    id=user.id if user.id is not None else 0,
                    username=user.username,
                    email=user.email,
                ),
            )

    async def logout(self, token: str) -> None:
        """Logout a user by invalidating their session."""
        if not self._initialized:
            await self.initialize()

        async with get_db_session() as session:
            await self.delete_session(session, token)

    async def get_current_user(self, token: str) -> UserResponse | None:
        """Get the current user from a token."""
        if not self._initialized:
            await self.initialize()

        async with get_db_session() as session:
            username = self.verify_token(token)
            if not username:
                return None

            result = await session.execute(select(User).where(col(User.username) == username))
            user = result.scalar_one_or_none()

            if user:
                return UserResponse(
                    id=user.id if user.id is not None else 0,
                    username=user.username,
                    email=user.email,
                )
            return None

    # API Key Methods
    def generate_api_key(self) -> tuple[str, str]:
        """Generate a secure API key and return (key, prefix)."""
        characters = string.ascii_letters + string.digits
        key = "".join(secrets.choice(characters) for _ in range(32))
        prefix = key[:8]
        api_key = f"{prefix}_{key[8:]}"
        return api_key, prefix

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key using bcrypt."""
        return bcrypt.hashpw(api_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def validate_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Validate an API key against its hash."""
        try:
            if not api_key or not hashed_key:
                return False
            return bcrypt.checkpw(api_key.encode("utf-8"), hashed_key.encode("utf-8"))
        except (ValueError, Exception):
            return False

    async def create_api_key(
        self,
        db: AsyncSession,
        user_id: int,
        name: str,
        scopes: list[str] | None = None,
        description: str | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key for a user."""
        # Validate user exists
        result = await db.execute(select(User).where(col(User.id) == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Check rate limit
        count_result = await db.execute(select(func.count()).where(col(APIKey.user_id) == user_id))
        key_count = count_result.scalar()
        if key_count and key_count >= 10:
            raise ValueError("Maximum number of API keys (10) reached for this user")

        # Validate scopes
        if not scopes:
            scopes = [ApiKeyScope.READ_SERVERS.value, ApiKeyScope.ACCESS_SERVERS.value]
        else:
            valid_scopes = {ApiKeyScope.READ_SERVERS.value, ApiKeyScope.ACCESS_SERVERS.value}
            for scope in scopes:
                if scope not in valid_scopes:
                    raise ValueError(f"Invalid scope: {scope}")

        # Generate API key
        api_key, prefix = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)

        # Create API key record
        api_key_record = APIKey(
            user_id=user_id,
            name=name,
            description=description,
            key_hash=key_hash,
            key_prefix=prefix,
            scopes=scopes,
            is_active=True,
        )

        db.add(api_key_record)
        await db.commit()
        await db.refresh(api_key_record)

        return api_key_record, api_key

    async def delete_api_key(self, db: AsyncSession, api_key_id: int, user_id: int) -> bool:
        """Delete an API key permanently."""
        result = await db.execute(
            select(APIKey).where(
                col(APIKey.id) == api_key_id,
                col(APIKey.user_id) == user_id,
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        await db.delete(api_key)
        await db.commit()

        return True

    async def get_user_api_keys(self, db: AsyncSession, user_id: int) -> list[APIKey]:
        """Get all API keys for a user."""
        query = select(APIKey).where(col(APIKey.user_id) == user_id)
        query = query.order_by(col(APIKey.created_at).desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def validate_api_key_for_request(
        self,
        db: AsyncSession,
        api_key: str,
        required_scopes: list[str] | None = None,
    ) -> tuple[bool, User | None, APIKey | None]:
        """Validate API key and return (is_valid, user, api_key_record)."""
        if not api_key:
            return False, None, None

        try:
            # Extract prefix from API key
            parts = api_key.split("_")
            if len(parts) != 2:
                return False, None, None

            prefix = parts[0]
            if len(prefix) != 8:
                return False, None, None

            # Use JOIN to fetch API key and user data efficiently
            query = (
                select(APIKey, User)
                .join(User)
                .where(
                    col(APIKey.key_prefix) == prefix,
                    col(APIKey.is_active),
                    col(User.is_active),
                )
            )
            result = await db.execute(query)
            row = result.first()

            if not row:
                return False, None, None

            api_key_record, user = row

            # Validate key hash
            if not self.validate_api_key(api_key, api_key_record.key_hash):
                return False, None, None

            # Check scopes
            if required_scopes:
                for scope in required_scopes:
                    if scope not in api_key_record.scopes:
                        return False, None, None

            # Update usage statistics
            api_key_record.last_used = datetime.now(UTC).replace(tzinfo=None)
            api_key_record.usage_count += 1
            db.add(api_key_record)
            await db.commit()

            return True, user, api_key_record

        except Exception:
            return False, None, None

    # High-level API Key Methods (from services layer)
    async def create_api_key_from_request(
        self, user_id: int, request: APIKeyCreateRequest, scopes: list[str] | None = None
    ) -> tuple[str, APIKeyResponse]:
        """Create a new API key from request."""
        if not self._initialized:
            await self.initialize()

        if scopes is None:
            scopes = [ApiKeyScope.READ_SERVERS.value, ApiKeyScope.ACCESS_SERVERS.value]

        async with get_db_session() as session:
            api_key_record, raw_key = await self.create_api_key(
                session, user_id, request.name, scopes, request.description
            )

            response = APIKeyResponse(
                id=api_key_record.id if api_key_record.id is not None else 0,
                name=api_key_record.name,
                description=api_key_record.description,
                key_prefix=api_key_record.key_prefix,
                key_hash=api_key_record.key_hash,
                scopes=api_key_record.scopes,
                is_active=api_key_record.is_active,
                created_at=api_key_record.created_at,
                last_used=api_key_record.last_used,
            )

            return raw_key, response

    async def get_user_api_keys_response(self, user_id: int) -> list[APIKeyResponse]:
        """Get all API keys for a user as response objects."""
        if not self._initialized:
            await self.initialize()

        async with get_db_session() as session:
            api_keys = await self.get_user_api_keys(session, user_id)

            return [
                APIKeyResponse(
                    id=key.id if key.id is not None else 0,
                    name=key.name,
                    description=key.description,
                    key_prefix=key.key_prefix,
                    key_hash=key.key_hash,
                    scopes=key.scopes,
                    is_active=key.is_active,
                    created_at=key.created_at,
                    last_used=key.last_used,
                )
                for key in api_keys
            ]

    async def delete_api_key_by_id(self, user_id: int, api_key_id: int) -> bool:
        """Delete an API key by ID."""
        if not self._initialized:
            await self.initialize()

        async with get_db_session() as session:
            return await self.delete_api_key(session, api_key_id, user_id)

    async def validate_api_key_with_scope(
        self, api_key: str, required_scope: str | None = None
    ) -> UserResponse | None:
        """Validate an API key and get the associated user."""
        if not self._initialized:
            await self.initialize()

        required_scopes = [required_scope] if required_scope else None
        async with get_db_session() as session:
            is_valid, user, _ = await self.validate_api_key_for_request(
                session, api_key, required_scopes
            )

            if is_valid and user:
                return UserResponse(
                    id=user.id if user.id is not None else 0,
                    username=user.username,
                    email=user.email,
                )

            return None

    # Utility Methods
    async def get_available_scopes(self) -> dict[str, str]:
        """Get all available API key scopes."""
        return {
            ApiKeyScope.READ_SERVERS.value: "Read server configurations and status",
            ApiKeyScope.ACCESS_SERVERS.value: "Access MCP servers for communication",
        }

    async def create_default_admin_user(self, db: AsyncSession) -> User:
        """Create the default admin user if it doesn't exist."""
        if not self.settings.admin_username:
            raise ValueError("Admin username is not configured")
        if not self.settings.admin_password:
            raise ValueError("Admin password is not configured")
        if not self.settings.admin_email:
            raise ValueError("Admin email is not configured")

        result = await db.execute(
            select(User).where(col(User.username) == self.settings.admin_username)
        )
        admin_user = result.scalar_one_or_none()

        if admin_user:
            return admin_user

        password_hash = self.get_password_hash(self.settings.admin_password)
        admin_user = User(
            username=self.settings.admin_username,
            password_hash=password_hash,
            email=self.settings.admin_email,
            is_active=True,
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        return admin_user

    async def create_default_admin_user_response(self) -> UserResponse:
        """Create the default admin user and return response."""
        if not self._initialized:
            await self.initialize()

        async with get_db_session() as session:
            user = await self.create_default_admin_user(session)
            return UserResponse(
                id=user.id if user.id is not None else 0,
                username=user.username,
                email=user.email,
            )


# Global singleton instance
_consolidated_auth_service = None


def get_consolidated_auth_service() -> ConsolidatedAuthService:
    """Get the singleton instance of ConsolidatedAuthService."""
    global _consolidated_auth_service
    if _consolidated_auth_service is None:
        _consolidated_auth_service = ConsolidatedAuthService()
    return _consolidated_auth_service


# FastAPI dependency
async def get_auth_service() -> ConsolidatedAuthService:
    """Get an authentication service instance."""
    service = get_consolidated_auth_service()
    await service.initialize()
    return service
