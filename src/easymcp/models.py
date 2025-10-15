"""Unified SQLModel models for the EasyMCP API."""

import re
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, field_validator
from sqlalchemy import Column
from sqlmodel import JSON, Field, Index, SQLModel


class ServerConfig(SQLModel, table=True):
    """Unified server configuration model using SQLModel."""

    __tablename__ = "server_configs"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, nullable=False)
    enabled: bool = Field(default=True)
    timeout: int = Field(default=60)

    # Transport configuration (unified storage)
    transport_type: str = Field(nullable=False)  # "stdio", "sse", "streamable-http"
    transport_config: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Optional authentication configuration
    auth_config: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        """Validate that timeout is within reasonable bounds."""
        if not isinstance(v, int):
            raise ValueError("timeout must be an integer")
        if v < 1:
            raise ValueError("timeout must be at least 1 second")
        if v > 3600:
            raise ValueError("timeout cannot exceed 3600 seconds (1 hour)")
        return v

    @field_validator("transport_type")
    @classmethod
    def validate_transport_type(cls, v):
        if v not in ["stdio", "sse", "streamable-http"]:
            raise ValueError(f"Invalid transport type: {v}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate server name format and length."""
        if not isinstance(v, str):
            raise ValueError("Server name must be a string")
        if not v.strip():
            raise ValueError("Server name cannot be empty")
        if len(v) > 64:
            raise ValueError("Server name must be 64 characters or less")
        # Allow alphanumeric characters, hyphens, underscores, and spaces
        if not re.match(r"^[a-zA-Z0-9 _-]+$", v):
            raise ValueError(
                "Server name must contain only alphanumeric characters, spaces, hyphens, "
                "and underscores"
            )
        return v.strip()

    @field_validator("transport_config")
    @classmethod
    def validate_transport_config(cls, v, info):
        transport_type = info.data.get("transport_type")
        if transport_type == "stdio" and "command" not in v:
            raise ValueError("stdio transport requires 'command' in config")
        elif transport_type == "sse" and "url" not in v:
            raise ValueError("sse transport requires 'url' in config")
        elif transport_type == "streamable-http" and "url" not in v:
            raise ValueError("streamable-http transport requires 'url' in config")
        return v


class LogLevel(str, Enum):
    """Available log levels for the application."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class GlobalConfig(SQLModel, table=True):
    """Global configuration model using SQLModel."""

    __tablename__ = "global_configs"

    id: int | None = Field(default=None, primary_key=True)
    stateless: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    pass_environment: bool = Field(default=False)
    auth: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate that log_level is one of the allowed values."""
        if not isinstance(v, str):
            raise ValueError("log_level must be a string")
        valid_levels = {level.value for level in LogLevel}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of: {', '.join(valid_levels)}")
        return v.upper()


# Pydantic models for API requests/responses (backward compatibility)
class StdioConfig(BaseModel):
    type: Literal["stdio"]
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    model_config = {"from_attributes": True}


class SseConfig(BaseModel):
    type: Literal["sse"]
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    model_config = {"from_attributes": True}


class ClientCredentialsGrantConfig(BaseModel):
    grant_type: Literal["client_credentials"] = "client_credentials"
    token_url: str
    client_id: str = Field(..., alias="clientId")
    client_secret: str = Field(..., alias="clientSecret")
    scope: str | None = None
    model_config = {"populate_by_name": True, "from_attributes": True}


class AuthorizationConfig(BaseModel):
    grant: ClientCredentialsGrantConfig
    model_config = {"from_attributes": True}


class StreamableHttpConfig(BaseModel):
    type: Literal["streamable-http"]
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    authorization: AuthorizationConfig | None = None
    model_config = {"from_attributes": True}


TransportConfig = StdioConfig | SseConfig | StreamableHttpConfig


class ServerConfigAPI(BaseModel):
    transport: TransportConfig = Field(..., discriminator="type")
    enabled: bool = True
    timeout: int = Field(
        default=60, ge=1, le=3600, description="Server timeout in seconds (1-3600)"
    )
    model_config = {"populate_by_name": True, "from_attributes": True}

    @classmethod
    def from_sqlmodel(cls, sql_model: ServerConfig) -> "ServerConfigAPI":
        """Convert SQLModel to API model."""
        transport_config = sql_model.transport_config
        transport_type = sql_model.transport_type

        # Create transport config based on type
        if transport_type == "stdio":
            transport: TransportConfig = StdioConfig.model_validate(
                {"type": "stdio", **transport_config}
            )
        elif transport_type == "sse":
            transport = SseConfig.model_validate({"type": "sse", **transport_config})
        elif transport_type == "streamable-http":
            transport_dict = {"type": "streamable-http", **transport_config}

            # Handle authorization if present
            if sql_model.auth_config:
                auth_data = sql_model.auth_config
                transport_dict["authorization"] = {
                    "grant": {
                        "grant_type": auth_data.get("grant_type", "client_credentials"),
                        "token_url": auth_data.get("token_url", ""),
                        "clientId": auth_data.get("client_id", ""),
                        "clientSecret": auth_data.get("client_secret", ""),
                        "scope": auth_data.get("scope"),
                    }
                }

            transport = StreamableHttpConfig.model_validate(transport_dict)
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

        return cls(
            transport=transport,
            enabled=sql_model.enabled,
            timeout=sql_model.timeout,
        )

    def to_sqlmodel(self, name: str) -> ServerConfig:
        """Convert API model to SQLModel."""
        transport_data = self.transport.model_dump(exclude={"type"})
        auth_config = None

        # Handle authorization for streamable-http
        if self.transport.type == "streamable-http" and self.transport.authorization:
            auth = self.transport.authorization.grant
            auth_config = {
                "grant_type": auth.grant_type,
                "token_url": auth.token_url,
                "client_id": auth.client_id,
                "client_secret": auth.client_secret,
                "scope": auth.scope,
            }

        return ServerConfig(
            name=name,
            enabled=self.enabled,
            timeout=self.timeout,
            transport_type=self.transport.type,
            transport_config=transport_data,
            auth_config=auth_config,
        )


class ServerStatus(BaseModel):
    id: str
    name: str
    state: str
    last_activity: str
    error: str | None = None
    endpoints: dict[str, str]
    capabilities: dict[str, int]


class StartServerRequest(BaseModel):
    stateless: bool = True
    allow_origins: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class McpServerList(BaseModel):
    servers: dict[str, dict]


class GlobalConfigAPI(BaseModel):
    stateless: bool = Field(default=True, description="Whether to run in stateless mode")
    log_level: LogLevel = Field(
        default=LogLevel.INFO, description="Logging level for the application"
    )
    pass_environment: bool = Field(
        default=False, description="Whether to pass environment variables to servers"
    )
    auth: dict[str, Any] = Field(default_factory=dict, description="Authentication configuration")
    model_config = {"from_attributes": True}

    @classmethod
    def from_sqlmodel(cls, sql_model: GlobalConfig) -> "GlobalConfigAPI":
        """Convert SQLModel to API model."""
        return cls.model_validate(
            {
                "stateless": sql_model.stateless,
                "log_level": sql_model.log_level,
                "pass_environment": sql_model.pass_environment,
                "auth": sql_model.auth,
            }
        )

    def to_sqlmodel(self) -> GlobalConfig:
        """Convert API model to SQLModel."""
        return GlobalConfig(
            stateless=self.stateless,
            log_level=self.log_level,
            pass_environment=self.pass_environment,
            auth=self.auth,
        )


class McpServersConfig(BaseModel):
    mcp_servers: dict[str, ServerConfigAPI] = Field(default_factory=dict, alias="mcpServers")
    model_config = {"populate_by_name": True, "validate_assignment": True}

    @property
    def servers(self) -> dict[str, ServerConfigAPI]:
        return self.mcp_servers


class SystemStatus(BaseModel):
    version: str
    api_last_activity: str
    server_instances: dict[str, str]
    uptime: float


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    checks: dict[str, str]


class SystemMetrics(BaseModel):
    timestamp: str
    servers: dict[str, int]
    requests: dict[str, int]
    performance: dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics including CPU, memory, and response times",
    )
    environment: dict[str, str] = Field(
        default_factory=dict, description="System environment information"
    )


class ServerCallCounts(BaseModel):
    """Call counts for tools, prompts, and resources for a specific server."""

    tools: int = 0
    prompts: int = 0
    resources: int = 0


class ServerStatistics(BaseModel):
    """Statistics for a specific MCP server."""

    name: str
    status: str
    call_counts: ServerCallCounts
    active_connections: int = 0
    uptime_seconds: float = 0
    last_activity: str


class McpStatistics(BaseModel):
    """Overall MCP statistics including all servers and client connections."""

    timestamp: str
    servers: dict[str, ServerStatistics]
    total_active_connections: int = 0
    total_calls: dict[str, int] = Field(
        default_factory=lambda: {"tools": 0, "prompts": 0, "resources": 0}
    )


# Authentication Models
class User(SQLModel, table=True):
    """User model for authentication."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False, max_length=50)
    password_hash: str = Field(nullable=False, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    last_login: datetime | None = None


class Session(SQLModel, table=True):
    """Session model for authentication."""

    __tablename__ = "sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    session_token: str = Field(unique=True, index=True, nullable=False, max_length=255)
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    last_accessed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    user_agent: str | None = None
    ip_address: str | None = None


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    email: str | None


# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    """Change password request model."""

    current_password: str
    new_password: str


# API Key Models
class ApiKeyScope(str, Enum):
    """Available scopes for API keys."""

    READ_SERVERS = "read:servers"
    ACCESS_SERVERS = "access:servers"


class APIKey(SQLModel, table=True):
    """API key model for authentication."""

    __tablename__ = "api_keys"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    name: str = Field(nullable=False, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    key_hash: str = Field(nullable=False, max_length=255)
    key_prefix: str = Field(nullable=False, max_length=8, index=True)
    scopes: list[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    last_used: datetime | None = None
    usage_count: int = Field(default=0)


# Pydantic models for API key requests and responses
class APIKeyCreateRequest(BaseModel):
    """Create API key request model."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class APIKeyResponse(BaseModel):
    """API key response model."""

    id: int
    name: str
    description: str | None
    key_prefix: str
    key_hash: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    last_used: datetime | None

    # Rate limiting information
    rate_limit_enabled: bool = True
    custom_limits: dict[str, Any] = Field(default_factory=dict)
    last_rate_limit_reset: datetime | None = None


class APIKeyListResponse(BaseModel):
    """API key list response model."""

    api_keys: list[APIKeyResponse]


class APIKeyCreatedResponse(BaseModel):
    """API key creation response model."""

    id: int
    name: str
    api_key: str
    key_prefix: str
    scopes: list[str]
    created_at: datetime
    rate_limit_enabled: bool = True
    custom_limits: dict[str, Any] = Field(default_factory=dict)
    message: str = "Store this API key securely. It will not be shown again."


class ScopeListResponse(BaseModel):
    """Available scopes response model."""

    scopes: dict[str, str] = Field(
        default_factory=lambda: {
            "read:servers": "Read server configurations and status",
            "write:servers": "Create, update, and delete servers",
        }
    )


# Update the create_indexes function to include API key and user indexes
def _create_indexes_with_api_keys():
    """Create database indexes for better query performance."""
    return [
        Index("idx_server_configs_name", ServerConfig.name),
        Index("idx_server_configs_transport_type", ServerConfig.transport_type),
        Index("idx_api_keys_key_prefix", APIKey.key_prefix),
    ]


# Create the indexes when the module is imported
DATABASE_INDEXES = _create_indexes_with_api_keys()
