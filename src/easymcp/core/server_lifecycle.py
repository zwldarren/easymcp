"""Server lifecycle management utilities."""

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from starlette.routing import BaseRoute

from ..mcp_stack.server import MCPServerSettings, create_mcp_app_stack
from ..models import ServerConfigAPI

logger = logging.getLogger(__name__)


@dataclass
class ServerStatistics:
    """Tracks server statistics and metrics."""

    name: str
    status: str = "stopped"
    call_counts: dict[str, int] = field(
        default_factory=lambda: {"tools": 0, "prompts": 0, "resources": 0}
    )
    active_connections: int = 0
    start_time: float | None = None
    last_activity: datetime | None = None

    def record_call(self, call_type: str) -> None:
        """Record a capability call."""
        if call_type in self.call_counts:
            self.call_counts[call_type] += 1
        self.last_activity = datetime.now(UTC)

    def update_connection(self, connected: bool) -> None:
        """Update connection count."""
        if connected:
            self.active_connections += 1
        else:
            self.active_connections = max(0, self.active_connections - 1)
        self.last_activity = datetime.now(UTC)

    def get_uptime_seconds(self) -> float:
        """Get server uptime in seconds."""
        if not self.start_time:
            return 0.0
        return time.time() - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "call_counts": self.call_counts.copy(),
            "active_connections": self.active_connections,
            "uptime_seconds": self.get_uptime_seconds(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else "",
        }


class ServerLifecycleManager:
    """Manages the lifecycle of MCP server instances."""

    def __init__(
        self,
        name: str,
        config: ServerConfigAPI,
        settings: MCPServerSettings,
        router: APIRouter,
        shutdown_event: asyncio.Event,
        extra_env: dict[str, str] | None = None,
    ):
        self.name = name
        self.config = config
        self.settings = settings
        self.router = router
        self.shutdown_event = shutdown_event
        self.extra_env = extra_env

        self.task: asyncio.Task | None = None
        self._stack: contextlib.AsyncExitStack | None = None
        self._server_shutdown_event = asyncio.Event()
        self.mounted_routes: list[BaseRoute] = []

        # Server state
        self.status = "stopped"
        self.endpoints: dict[str, str] = field(default_factory=dict)
        self.capabilities: dict[str, int] = field(default_factory=dict)

        # Statistics
        self.statistics = ServerStatistics(name=self.name)

    async def start(self) -> None:
        """Start the MCP server in a background task."""
        if self.status == "running":
            logger.warning(f"Server '{self.name}' is already running.")
            return

        self.status = "starting"
        started_event = asyncio.Event()
        startup_error_queue: asyncio.Queue[Exception] = asyncio.Queue()

        self.task = asyncio.create_task(
            self._run_and_manage_resources(started_event, startup_error_queue)
        )

        # Wait for the server to be set up
        await started_event.wait()

        # Check if an error occurred during startup
        if not startup_error_queue.empty():
            err = await startup_error_queue.get()
            raise err

    async def stop(self) -> None:
        """Stop the MCP server."""
        if self.status not in ["running", "starting", "error"]:
            return

        # Signal shutdown to the server task
        self._server_shutdown_event.set()

        if self.task and not self.task.done():
            try:
                # Wait for the task to complete gracefully
                await asyncio.wait_for(self.task, timeout=5.0)
            except TimeoutError:
                self.task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.task
            except Exception as e:
                logger.exception(f"Error while stopping server '{self.name}': {e}")

        self.task = None

    async def _run_and_manage_resources(
        self,
        started_event: asyncio.Event,
        startup_error_queue: asyncio.Queue[Exception],
    ) -> None:
        """The background task that manages the server's lifecycle."""
        self._stack = contextlib.AsyncExitStack()
        try:
            from ..core.server_params import api_config_to_mcp_params

            params = api_config_to_mcp_params(self.config, self.extra_env)
            mcp_server_params = {self.name: params}

            # Create the MCP app stack
            self._app = await self._stack.enter_async_context(
                create_mcp_app_stack(
                    self.settings,
                    mcp_server_params=mcp_server_params,
                )
            )

            if not self._app or not self._app.routes:
                raise RuntimeError(f"Failed to create Starlette app for server '{self.name}'.")

            # Mount routes
            self.mounted_routes = self._app.routes
            self.router.routes.extend(self.mounted_routes)

            # Update server state
            self.status = "running"
            self.statistics.status = "running"
            self.statistics.start_time = time.time()
            self.statistics.last_activity = datetime.now(UTC)

            # Set up endpoints
            base_url = f"http://{self.settings.bind_host}:{self.settings.port}"
            path_prefix = f"/servers/{self.name}"
            self.endpoints = {
                "mcp": f"{base_url}{path_prefix}/mcp",
            }

            # Get capabilities
            self.capabilities = await self._get_capability_counts()

            # Register statistics callbacks
            await self._register_statistics_callbacks()

            # Signal that startup is complete
            started_event.set()

            # Wait until shutdown is signaled
            await self._server_shutdown_event.wait()

        except asyncio.CancelledError:
            logger.debug(f"Server task cancelled for '{self.name}'")
        except Exception as e:
            self.status = "error"
            self.statistics.status = "error"
            logger.exception(f"Failed to start server '{self.name}'")
            # Signal startup failure
            await startup_error_queue.put(e)
            started_event.set()  # Also set event to unblock `start`
        finally:
            logger.info(f"Starting cleanup for server '{self.name}' (status: {self.status})")

            # Unmount routes
            if self.mounted_routes:
                original_routes = self.router.routes[:]
                routes_removed = 0
                new_routes = []
                for route in original_routes:
                    if route in self.mounted_routes:
                        routes_removed += 1
                    else:
                        new_routes.append(route)

                self.router.routes = new_routes
                self.mounted_routes = []
                logger.debug(f"Unmounted {routes_removed} routes for server '{self.name}'")

            # Clean up stack
            if self._stack:
                try:
                    await asyncio.wait_for(self._stack.aclose(), timeout=2.0)
                    logger.debug(f"Successfully cleaned up stack for server '{self.name}'")
                except TimeoutError:
                    logger.warning(f"Stack cleanup timeout for server '{self.name}', forcing exit")
                except Exception as e:
                    logger.exception(f"Error during stack cleanup for server '{self.name}': {e}")

            # Unregister statistics callbacks to prevent memory leaks
            try:
                await self._unregister_statistics_callbacks()
            except Exception as e:
                logger.warning(f"Failed to unregister statistics callbacks for '{self.name}': {e}")

            # Update status
            if self.status != "error":
                self.status = "stopped"
                self.statistics.status = "stopped"
                logger.info(f"Server '{self.name}' cleanup completed")

    async def _get_capability_counts(self) -> dict[str, int]:
        """Get actual counts of tools, prompts, and resources from the MCP server."""
        from ..mcp_stack.server import get_capability_counts

        counts = get_capability_counts(self.name)
        if not counts:
            return {
                "prompts": 0,
                "resources": 0,
                "tools": 0,
            }
        return {
            "prompts": counts.get("prompts", 0),
            "resources": counts.get("resources", 0),
            "tools": counts.get("tools", 0),
        }

    async def _register_statistics_callbacks(self) -> None:
        """Register statistics callbacks for this server."""
        from ..mcp_stack.server import register_statistics_callbacks

        await register_statistics_callbacks(
            self.name,
            self.statistics.record_call,
            self.statistics.update_connection,
        )

    async def _unregister_statistics_callbacks(self) -> None:
        """Unregister statistics callbacks for this server."""
        from ..mcp_stack.server import unregister_statistics_callbacks

        await unregister_statistics_callbacks(self.name)
