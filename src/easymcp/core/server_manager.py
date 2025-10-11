"""Unified server management and configuration service."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter

from ..core.errors import (
    ConfigurationError,
    ServerAlreadyRunningError,
    ServerNotFoundError,
    ServerNotRunningError,
)
from ..core.server_lifecycle import ServerLifecycleManager
from ..mcp_stack.server import MCPServerSettings
from ..models import (
    GlobalConfigAPI,
    ServerConfigAPI,
    ServerStatus,
    StartServerRequest,
)
from ..services.config_service import ConsolidatedConfigService, get_config_service

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ManagedServer:
    """Wrapper for server lifecycle management with simplified interface."""

    name: str
    config: ServerConfigAPI
    settings: MCPServerSettings
    router: APIRouter
    shutdown_event: asyncio.Event
    extra_env: dict[str, str] | None = None

    def __post_init__(self):
        """Initialize the lifecycle manager."""
        self._lifecycle_manager = ServerLifecycleManager(
            name=self.name,
            config=self.config,
            settings=self.settings,
            router=self.router,
            shutdown_event=self.shutdown_event,
            extra_env=self.extra_env,
        )

    @property
    def status(self) -> str:
        """Get the current server status."""
        return self._lifecycle_manager.status

    @property
    def endpoints(self) -> dict[str, str]:
        """Get the server endpoints."""
        return self._lifecycle_manager.endpoints

    @property
    def capabilities(self) -> dict[str, int]:
        """Get the server capabilities."""
        return self._lifecycle_manager.capabilities

    @property
    def last_activity(self) -> datetime | None:
        """Get the last activity timestamp."""
        return self._lifecycle_manager.statistics.last_activity

    async def start(self) -> None:
        """Start the MCP server."""
        await self._lifecycle_manager.start()

    async def stop(self) -> None:
        """Stop the MCP server."""
        await self._lifecycle_manager.stop()

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive statistics for this server."""
        return self._lifecycle_manager.statistics.to_dict()

    def record_call(self, call_type: str) -> None:
        """Record a capability call for statistics."""
        self._lifecycle_manager.statistics.record_call(call_type)

    def update_connection(self, connected: bool) -> None:
        """Update connection count for statistics."""
        self._lifecycle_manager.statistics.update_connection(connected)


class ServerManager:
    """Unified server management and configuration service."""

    def __init__(self, router: APIRouter, shutdown_event: asyncio.Event):
        """Initialize the ServerManager."""
        self.router = router
        self.shutdown_event = shutdown_event
        self.servers: dict[str, ManagedServer] = {}
        self._config_service: ConsolidatedConfigService | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the server manager with unified configuration service."""
        if self._initialized:
            return

        self._config_service = await get_config_service()
        self._initialized = True
        logger.info("ServerManager initialized with unified configuration service")

    # --- Configuration Management Properties ---
    @property
    def configs(self) -> dict[str, ServerConfigAPI]:
        """Get all server configurations (read-only)."""
        if not self._initialized:
            raise RuntimeError("ServerManager not initialized")
        if not self._config_service:
            raise RuntimeError("Config service not initialized")
        return self._config_service.configs

    @property
    def global_config(self) -> GlobalConfigAPI:
        """Get global configuration (read-only)."""
        if not self._initialized:
            raise RuntimeError("ServerManager not initialized")
        if not self._config_service:
            raise RuntimeError("Config service not initialized")
        return self._config_service.global_config

    # --- Server Lifecycle Management Methods ---

    def get_server_status(self, name: str) -> ServerStatus:
        """Get the status of a specific server."""
        if name in self.servers:
            managed_server = self.servers[name]
            return ServerStatus(
                id=name,
                name=name,
                state=managed_server.status,
                last_activity=managed_server.last_activity.isoformat()
                if managed_server.last_activity
                else "",
                error=None if managed_server.status != "error" else "Server error",
                endpoints=managed_server.endpoints,
                capabilities=managed_server.capabilities,
            )
        if name in self.configs:
            return ServerStatus(
                id=name,
                name=name,
                state="stopped",
                last_activity="",
                error=None,
                endpoints={},
                capabilities={},
            )
        raise ValueError(f"Server '{name}' not found")

    async def start_server(self, name: str, request: StartServerRequest) -> ServerStatus:
        """Start a specific server with guaranteed configuration consistency."""
        if not self._initialized:
            await self.initialize()

        if name not in self.configs:
            raise ServerNotFoundError(f"Server '{name}' not found in configuration")

        if name in self.servers and self.servers[name].status == "running":
            raise ServerAlreadyRunningError(f"Server '{name}' is already running")

        # Get the current config from the unified service
        config = self.configs[name]
        if not config.enabled:
            # Update the configuration to enable the server
            config.enabled = True
            if self._config_service is None:
                raise RuntimeError("Config service not initialized")
            await self._config_service.update_server_config(name, config)
            # The config is now updated atomically in both database and memory

        # Get global config from the unified service
        global_config = self.global_config

        settings = MCPServerSettings(
            bind_host="localhost",
            port=0,  # Use ephemeral port
            stateless=global_config.stateless,
            allow_origins=request.allow_origins,
            log_level="INFO",
            shutdown_event=self.shutdown_event,
        )

        managed_server = ManagedServer(
            name=name,
            config=config,
            settings=settings,
            router=self.router,
            shutdown_event=self.shutdown_event,
            extra_env=request.env,
        )

        self.servers[name] = managed_server

        try:
            await managed_server.start()
            return self.get_server_status(name)
        except Exception as e:
            logger.exception(f"Failed to start server '{name}'")
            if name in self.servers:
                del self.servers[name]
            raise ConfigurationError(f"Failed to start server '{name}': {e}") from e

    async def stop_server(self, name: str, persist: bool = True) -> ServerStatus:
        """Stop a specific server, with an option to persist the stopped state."""
        if not self._initialized:
            await self.initialize()

        if name not in self.servers:
            raise ServerNotRunningError(f"Server '{name}' is not running")

        managed_server = self.servers[name]
        try:
            await managed_server.stop()
            del self.servers[name]

            if persist and name in self.configs:
                config = self.configs[name]
                config.enabled = False
                if self._config_service is None:
                    raise RuntimeError("Config service not initialized")
                await self._config_service.update_server_config(name, config)

            return self.get_server_status(name)
        except Exception as e:
            logger.exception(f"Failed to stop server '{name}'")
            raise ConfigurationError(f"Failed to stop server '{name}': {e}") from e

    async def stop_all_servers(self) -> None:
        """Stop all running servers without changing their persistent enabled state."""
        stop_tasks = [
            self.stop_server(name, persist=False)
            for name, server in self.servers.items()
            if server.status in ["running", "starting"]
        ]
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def close(self) -> None:
        """Close the server manager."""
        await self.stop_all_servers()
        self.servers.clear()

    def get_all_servers_status(self) -> dict[str, ServerStatus]:
        """Get status of all servers."""
        status = {}
        all_server_names = set(self.configs.keys()) | set(self.servers.keys())
        for name in all_server_names:
            try:
                status[name] = self.get_server_status(name)
            except ValueError:
                logger.warning(f"Could not get status for server '{name}', skipping.")
        return status

    def get_all_servers_statistics(self) -> dict[str, dict[str, Any]]:
        """Get comprehensive statistics for all servers."""
        stats = {}
        all_server_names = set(self.configs.keys()) | set(self.servers.keys())

        for name in all_server_names:
            if name in self.servers:
                # Server is running, get real-time statistics
                stats[name] = self.servers[name].get_statistics()
            else:
                # Server is not running, provide basic info
                stats[name] = {
                    "name": name,
                    "status": "stopped",
                    "call_counts": {"tools": 0, "prompts": 0, "resources": 0},
                    "active_connections": 0,
                    "uptime_seconds": 0.0,
                    "last_activity": "",
                }

        return stats

    def record_server_call(self, server_name: str, call_type: str) -> None:
        """Record a call to a specific server's capability."""
        if server_name in self.servers:
            self.servers[server_name].record_call(call_type)

    def record_server_connection(self, server_name: str, connected: bool) -> None:
        """Record a connection change for a specific server."""
        if server_name in self.servers:
            self.servers[server_name].update_connection(connected)
