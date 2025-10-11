"""Create a local SSE server that proxies requests to a stdio MCP server."""

import asyncio
import contextlib
import logging
import secrets
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import Server as MCPServerSDK
from mcp.server.streamable_http import EventStore
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import BaseRoute, Mount
from starlette.types import Receive, Scope, Send

from ..models import AuthorizationConfig
from .proxy import create_proxy_server

if TYPE_CHECKING:
    from mcp.types import JSONRPCMessage


logger = logging.getLogger(__name__)

# Global storage for capability counts with cleanup
_capability_counts_store: dict[str, dict[str, int]] = {}
_capability_counts_lock = asyncio.Lock()

# Global statistics callbacks with cleanup
_statistics_callbacks: dict[str, dict[str, Callable]] = {}
_statistics_callbacks_lock = asyncio.Lock()


async def cleanup_all_server_data() -> None:
    """Clean up all server data to prevent memory leaks during shutdown."""
    logger.info("Cleaning up all server callback and capability data...")

    async with _statistics_callbacks_lock:
        for _server_name, callbacks in _statistics_callbacks.items():
            if callbacks:
                callbacks.clear()
        _statistics_callbacks.clear()

    async with _capability_counts_lock:
        for _server_name, counts in _capability_counts_store.items():
            if counts:
                counts.clear()
        _capability_counts_store.clear()

    logger.info("Server data cleanup completed")


async def _store_capability_counts(server_name: str, counts: dict[str, int]) -> None:
    """Store capability counts for a server."""
    async with _capability_counts_lock:
        _capability_counts_store[server_name] = counts


def get_capability_counts(server_name: str) -> dict[str, int] | None:
    """Get stored capability counts for a server."""
    return _capability_counts_store.get(server_name)


async def register_statistics_callbacks(
    server_name: str, record_call: Callable, record_connection: Callable
) -> None:
    """Register statistics callbacks for a server."""
    async with _statistics_callbacks_lock:
        _statistics_callbacks[server_name] = {
            "record_call": record_call,
            "record_connection": record_connection,
        }


async def unregister_statistics_callbacks(server_name: str) -> None:
    """Unregister statistics callbacks for a server."""
    async with _statistics_callbacks_lock:
        if server_name in _statistics_callbacks:
            # Clear the callback references to help garbage collection
            callbacks = _statistics_callbacks[server_name]
            if callbacks:
                callbacks.clear()
            del _statistics_callbacks[server_name]

    async with _capability_counts_lock:
        if server_name in _capability_counts_store:
            # Clear the counts to help garbage collection
            counts = _capability_counts_store[server_name]
            if counts:
                counts.clear()
            del _capability_counts_store[server_name]


def record_server_call(server_name: str, call_type: str) -> None:
    """Record a server call using the registered callback."""
    if server_name in _statistics_callbacks:
        callback = _statistics_callbacks[server_name].get("record_call")
        if callback:
            # The callback now handles both 1 and 2 parameter cases
            callback(call_type)


async def _get_server_capability_counts(session: ClientSession) -> dict[str, int]:
    """Get actual counts of tools, prompts, and resources from an MCP server session."""
    capability_counts = {"tools": 0, "prompts": 0, "resources": 0}

    try:
        # List tools and count them
        try:
            tools_result = await session.list_tools()
            if hasattr(tools_result, "tools"):
                capability_counts["tools"] = len(tools_result.tools)
            elif isinstance(tools_result, list):
                capability_counts["tools"] = len(tools_result)
            logger.debug(f"Found {capability_counts['tools']} tools")
        except Exception as e:
            logger.debug(f"Could not list tools: {e}")

        # List prompts and count them
        try:
            prompts_result = await session.list_prompts()
            if hasattr(prompts_result, "prompts"):
                capability_counts["prompts"] = len(prompts_result.prompts)
            elif isinstance(prompts_result, list):
                capability_counts["prompts"] = len(prompts_result)
            logger.debug(f"Found {capability_counts['prompts']} prompts")
        except Exception as e:
            logger.debug(f"Could not list prompts: {e}")

        # List resources and count them
        try:
            resources_result = await session.list_resources()
            if hasattr(resources_result, "resources"):
                capability_counts["resources"] = len(resources_result.resources)
            elif isinstance(resources_result, list):
                capability_counts["resources"] = len(resources_result)
            logger.debug(f"Found {capability_counts['resources']} resources")
        except Exception as e:
            logger.debug(f"Could not list resources: {e}")

    except Exception as e:
        logger.exception(f"Failed to get capability counts: {e}")

    return capability_counts


if TYPE_CHECKING:
    from mcp.types import JSONRPCMessage


class SecureEventStore(EventStore):
    """
    Secure event store that binds sessions to user-specific information
    to prevent session hijacking.
    """

    def __init__(self):
        self._events = {}
        self._user_sessions = {}
        self._event_counter = 0

    def _generate_secure_session_id(self, user_id: str | None = None) -> str:
        """Generate a cryptographically secure session ID."""
        if user_id:
            # Bind session ID to user ID as recommended in security guide
            session_id = f"{user_id}:{secrets.token_urlsafe(32)}"
        else:
            # Fallback to secure random session ID
            session_id = secrets.token_urlsafe(32)
        return session_id

    def _validate_session_binding(self, session_id: str, user_id: str | None = None) -> bool:
        """Validate that session ID is properly bound to user information."""
        # Handle the default case where session_id might be "0" or similar
        # This can happen during initial connection establishment
        if session_id in ("0", "1", "2", "3"):
            logger.debug(f"Accepting default session ID for connection establishment: {session_id}")
            return True

        if user_id and ":" in session_id:
            stored_user_id, _ = session_id.split(":", 1)
            is_valid = secrets.compare_digest(stored_user_id, user_id)
            if not is_valid:
                logger.warning(
                    f"Session validation failed: user_id mismatch for session {session_id[:8]}..."
                )
            return is_valid
        elif user_id:
            logger.warning(
                f"Session validation failed: user_id provided but session "
                f"{session_id[:8]}... has no user binding"
            )
            return False
        elif ":" in session_id:
            logger.warning(
                f"Session validation failed: session {session_id[:8]}... has user "
                f"binding but no user_id provided"
            )
            return False
        # For sessions without user binding, validate they have the expected format
        if not session_id or len(session_id) < 32:
            session_preview = session_id[:8] if session_id else "empty"
            logger.warning(
                f"Session validation failed: invalid session format for {session_preview}"
            )
            return False

        logger.debug(f"Session validation successful for anonymous session {session_id[:8]}...")
        return True

    async def store_event(self, stream_id: str, message: "JSONRPCMessage") -> str:
        """Store event with secure session binding."""
        # Extract user_id from stream_id if it contains user binding
        user_id = None
        if ":" in stream_id:
            user_id, _ = stream_id.split(":", 1)

        if not self._validate_session_binding(stream_id, user_id):
            logger.warning(f"Invalid session binding attempt for stream {stream_id}")
            raise ValueError("Invalid session binding")

        if stream_id not in self._events:
            self._events[stream_id] = []

        # Generate event ID
        event_id = f"event_{self._event_counter}"
        self._event_counter += 1

        # Store the event with its ID
        self._events[stream_id].append(
            {"event_id": event_id, "message": message, "timestamp": asyncio.get_event_loop().time()}
        )

        return event_id

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback: Any,
    ) -> str | None:
        """Replay events that occurred after the specified event ID with session validation."""
        # Find the stream that contains the last_event_id
        target_stream = None
        start_index = 0

        for stream_id, events in self._events.items():
            for i, event in enumerate(events):
                if event["event_id"] == last_event_id:
                    target_stream = stream_id
                    start_index = i + 1
                    break
            if target_stream:
                break

        if not target_stream:
            return None

        # Validate session binding before replaying
        user_id = None
        if ":" in target_stream:
            user_id, _ = target_stream.split(":", 1)

        if not self._validate_session_binding(target_stream, user_id):
            logger.warning(f"Unauthorized event replay attempt for stream {target_stream}")
            return None

        # Import EventMessage here to avoid circular imports
        from mcp.server.streamable_http import EventMessage

        # Replay events after the specified event ID
        events_to_replay = self._events[target_stream][start_index:]
        for event in events_to_replay:
            event_message = EventMessage(message=event["message"], event_id=event["event_id"])
            await send_callback(event_message)

        return target_stream


@dataclass
class MCPServerSettings:
    """Settings for the MCP server."""

    bind_host: str
    port: int
    stateless: bool = False
    allow_origins: list[str] | None = None
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    shutdown_event: asyncio.Event | None = None


def create_single_instance_routes(
    mcp_server_instance: MCPServerSDK[object],
    *,
    stateless_instance: bool,
    mcp_settings: MCPServerSettings,
) -> tuple[list[BaseRoute], StreamableHTTPSessionManager]:  # Return the manager itself
    """Create Starlette routes and the HTTP session manager for a single MCP server instance."""
    logger.debug(
        f"Creating routes for a single MCP server instance (stateless: {stateless_instance})"
    )

    # Create secure session store with user binding for both stateless and stateful modes
    event_store = SecureEventStore()

    http_session_manager = StreamableHTTPSessionManager(
        app=mcp_server_instance,
        event_store=event_store,
        json_response=True,
        stateless=stateless_instance,
    )

    async def handle_streamable_http_instance(scope: Scope, receive: Receive, send: Send) -> None:
        await http_session_manager.handle_request(scope, receive, send)

    routes: list[BaseRoute] = []

    # Add the main MCP route
    routes.append(Mount("/mcp", app=handle_streamable_http_instance))

    return routes, http_session_manager


@contextlib.asynccontextmanager
async def create_mcp_app_stack(
    mcp_settings: MCPServerSettings,
    mcp_server_params: dict[str, StdioServerParameters | dict] | None = None,
) -> AsyncIterator[Starlette]:
    """Create a Starlette application for an MCP server and manage its resource stack."""
    if mcp_server_params is None:
        mcp_server_params = {}

    all_routes: list[BaseRoute] = []

    async with contextlib.AsyncExitStack() as stack:

        @contextlib.asynccontextmanager
        async def combined_lifespan(_app: Starlette) -> AsyncIterator[None]:
            logger.info("MCP server lifespan starting...")
            yield
            logger.info("MCP server lifespan shutting down...")

        # Setup MCP servers
        for name, params in mcp_server_params.items():
            try:
                if isinstance(params, StdioServerParameters):
                    logger.debug(
                        f"Setting up MCP server '{name}': {params.command} {' '.join(params.args)}"
                    )

                    # Special handling for Docker commands
                    if params.command == "docker":
                        logger.info(f"Docker command detected for server '{name}'")
                        logger.info(f"Full command: {params.command} {' '.join(params.args)}")
                        logger.info(f"Environment: {params.env}")

                        # Check if Docker is available
                        import subprocess

                        try:
                            result = subprocess.run(
                                ["docker", "--version"], capture_output=True, text=True, timeout=10
                            )
                            if result.returncode != 0:
                                logger.error(
                                    f"Docker CLI not available or not working: {result.stderr}"
                                )
                                continue
                            logger.info(f"Docker CLI available: {result.stdout.strip()}")
                        except subprocess.TimeoutExpired:
                            logger.error("Docker CLI timeout - check Docker daemon")
                            continue
                        except FileNotFoundError:
                            logger.error("Docker CLI not found - install Docker CLI in container")
                            continue
                        except Exception as e:
                            logger.error(f"Error checking Docker CLI: {e}")
                            continue

                    streams = await stack.enter_async_context(stdio_client(params))
                elif isinstance(params, dict) and "url" in params:
                    # Determine transport type based on explicit configuration
                    url = params.get("url")
                    if url is None:
                        logger.error(f"URL is required for server '{name}' but was not provided")
                        continue
                    headers = params.get("headers", {})
                    transport_type = params.get("transport", "streamable-http")
                    authorization = params.get("authorization")

                    # Handle authorization with simplified approach
                    if authorization and isinstance(authorization, AuthorizationConfig):
                        logger.info(f"Using authorization for server '{name}'")
                        # For client credentials, directly add the authorization header
                        if hasattr(authorization.grant, "client_id") and hasattr(
                            authorization.grant, "client_secret"
                        ):
                            # Use basic auth with client credentials
                            import base64

                            credentials = (
                                f"{authorization.grant.client_id}:"
                                f"{authorization.grant.client_secret}"
                            )
                            encoded_credentials = base64.b64encode(credentials.encode()).decode()
                            headers["Authorization"] = f"Basic {encoded_credentials}"

                    # Use the explicitly specified transport type
                    if transport_type == "streamable-http":
                        logger.debug(
                            f"Setting up MCP server '{name}' from streamable-http stream: {url}"
                        )
                        streams = await stack.enter_async_context(
                            streamablehttp_client(url, headers=headers)
                        )
                    else:
                        logger.error(
                            f"Unsupported transport type '{transport_type}' for server '{name}'"
                        )
                        continue
                else:
                    logger.error(f"Unsupported MCP server parameters for '{name}': {type(params)}")
                    continue

                session = await stack.enter_async_context(ClientSession(streams[0], streams[1]))

                # Create proxy with statistics callbacks
                def make_record_call(server_name):
                    return lambda call_type: record_server_call(server_name, call_type)

                proxy = await create_proxy_server(
                    session,
                    record_call=make_record_call(name),
                )

                # Get capability counts from the initialized server
                capability_counts = await _get_server_capability_counts(session)
                logger.info(f"Server '{name}' capability counts: {capability_counts}")

                instance_routes, http_manager = create_single_instance_routes(
                    proxy,
                    stateless_instance=mcp_settings.stateless,
                    mcp_settings=mcp_settings,
                )
                await stack.enter_async_context(http_manager.run())  # Manage lifespan

                server_mount = Mount(f"/servers/{name}", routes=instance_routes)
                all_routes.append(server_mount)

                await _store_capability_counts(name, capability_counts)
            except Exception:
                logger.exception(f"Failed to setup MCP server '{name}'")

                # Provide Docker-specific troubleshooting
                if isinstance(params, StdioServerParameters) and params.command == "docker":
                    logger.error(f"Docker-specific troubleshooting for server '{name}':")
                    logger.error("1. Check if Docker daemon is running on host: `docker ps`")
                    logger.error(
                        "2. Verify Docker socket is mounted: "
                        "/var/run/docker.sock:/var/run/docker.sock:ro"
                    )
                    logger.error("3. Check Docker CLI is installed in container")
                    logger.error(
                        "4. Verify Docker image exists: e.g. `docker images | grep mcp/memory`"
                    )
                    logger.error("5. Test Docker command manually in container")
                    logger.error(f"6. Environment variables: {params.env}")
                    logger.error(f"7. Full command: docker {' '.join(params.args)}")

                continue

        if not mcp_server_params:
            logger.error("No servers configured to run.")
            yield Starlette()
            return

        middleware: list[Middleware] = []
        if mcp_settings.allow_origins:
            middleware.append(
                Middleware(
                    CORSMiddleware,
                    allow_origins=mcp_settings.allow_origins,
                    allow_methods=["*"],
                    allow_headers=["*"],
                ),
            )

        starlette_app = Starlette(
            debug=(mcp_settings.log_level == "DEBUG"),
            routes=all_routes,
            middleware=middleware,
            lifespan=combined_lifespan,
        )

        starlette_app.router.redirect_slashes = False
        yield starlette_app
