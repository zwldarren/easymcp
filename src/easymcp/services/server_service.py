"""Server service for managing MCP server lifecycle and operations.

This service provides a high-level interface for managing MCP servers,
abstracting away the complexity of server lifecycle management.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.server_manager import ServerManager
from ..models import (
    ServerConfigAPI,
    ServerStatistics,
    ServerStatus,
    StartServerRequest,
)
from .config_service import ConsolidatedConfigService as ConfigService

logger = logging.getLogger(__name__)


class ServerService:
    """Service for managing MCP server operations."""

    def __init__(self, server_manager: "ServerManager", config_service: ConfigService):
        """Initialize the server service.

        Args:
            server_manager: Server manager instance
            config_service: Configuration service instance
        """
        self._server_manager = server_manager
        self._config_service = config_service
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the server service."""
        if self._initialized:
            return

        # Ensure dependencies are initialized
        if not self._config_service.is_initialized:
            await self._config_service.initialize()

        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    # Server Lifecycle Methods
    async def start_server(
        self, name: str, request: StartServerRequest | None = None
    ) -> ServerStatus:
        """Start a configured server.

        Args:
            name: Server name
            request: Start request parameters

        Returns:
            Server status after starting
        """
        if not self._initialized:
            await self.initialize()

        # Get server configuration
        config = await self._config_service.get_server_config(name)
        if not config:
            raise ValueError(f"Server configuration not found: {name}")

        # Use default request if not provided
        if request is None:
            request = StartServerRequest()

        return await self._server_manager.start_server(name, request)

    async def stop_server(self, name: str, persist: bool = True) -> ServerStatus:
        """Stop a running server.

        Args:
            name: Server name
            persist: Whether to persist the stopped state

        Returns:
            Server status after stopping
        """
        if not self._initialized:
            await self.initialize()

        return await self._server_manager.stop_server(name, persist)

    async def restart_server(self, name: str) -> ServerStatus:
        """Restart a server.

        Args:
            name: Server name

        Returns:
            Server status after restart
        """
        if not self._initialized:
            await self.initialize()

        # Stop the server first
        await self.stop_server(name, persist=False)

        # Start it again
        return await self.start_server(name)

    async def stop_all_servers(self) -> None:
        """Stop all running servers."""
        if not self._initialized:
            await self.initialize()

        await self._server_manager.stop_all_servers()

    # Server Status Methods
    async def get_server_status(self, name: str) -> ServerStatus:
        """Get the status of a specific server.

        Args:
            name: Server name

        Returns:
            Current server status
        """
        if not self._initialized:
            await self.initialize()

        return self._server_manager.get_server_status(name)

    async def get_all_servers_status(self) -> dict[str, ServerStatus]:
        """Get the status of all servers.

        Returns:
            Dictionary mapping server names to their status
        """
        if not self._initialized:
            await self.initialize()

        return self._server_manager.get_all_servers_status()

    async def get_running_servers(self) -> list[str]:
        """Get list of currently running server names.

        Returns:
            List of running server names
        """
        if not self._initialized:
            await self.initialize()

        all_status = await self.get_all_servers_status()
        return [
            name for name, status in all_status.items() if status.state in ("running", "starting")
        ]

    async def get_stopped_servers(self) -> list[str]:
        """Get list of stopped server names.

        Returns:
            List of stopped server names
        """
        if not self._initialized:
            await self.initialize()

        all_status = await self.get_all_servers_status()
        return [name for name, status in all_status.items() if status.state == "stopped"]

    # Server Configuration Methods
    async def get_server_config(self, name: str) -> ServerConfigAPI | None:
        """Get server configuration.

        Args:
            name: Server name

        Returns:
            Server configuration or None if not found
        """
        if not self._initialized:
            await self.initialize()

        return await self._config_service.get_server_config(name)

    async def update_server_config(self, name: str, config: ServerConfigAPI) -> ServerConfigAPI:
        """Update server configuration.

        Args:
            name: Server name
            config: New server configuration

        Returns:
            Updated configuration
        """
        if not self._initialized:
            await self.initialize()

        return await self._config_service.update_server_config(name, config)

    # Server Statistics Methods
    async def get_server_statistics(self, name: str) -> ServerStatistics | None:
        """Get statistics for a specific server.

        Args:
            name: Server name

        Returns:
            Server statistics or None if server not found
        """
        if not self._initialized:
            await self.initialize()

        all_stats = self._server_manager.get_all_servers_statistics()
        if name in all_stats:
            data = all_stats[name]
            return ServerStatistics(
                name=name,
                status=data.get("status", "unknown"),
                call_counts=data.get("call_counts", {}),
                active_connections=data.get("active_connections", 0),
                uptime_seconds=data.get("uptime_seconds", 0),
                last_activity=data.get("last_activity", ""),
            )
        return None

    async def get_all_servers_statistics(self) -> dict[str, ServerStatistics]:
        """Get statistics for all servers.

        Returns:
            Dictionary mapping server names to their statistics
        """
        if not self._initialized:
            await self.initialize()

        all_stats = self._server_manager.get_all_servers_statistics()
        result = {}

        for name, data in all_stats.items():
            result[name] = ServerStatistics(
                name=name,
                status=data.get("status", "unknown"),
                call_counts=data.get("call_counts", {}),
                active_connections=data.get("active_connections", 0),
                uptime_seconds=data.get("uptime_seconds", 0),
                last_activity=data.get("last_activity", ""),
            )

        return result

    # Utility Methods
    async def validate_server_before_start(self, name: str) -> tuple[bool, str]:
        """Validate that a server can be started.

        Args:
            name: Server name

        Returns:
            Tuple of (can_start, error_message)
        """
        if not self._initialized:
            await self.initialize()

        # Check if configuration exists
        config = await self._config_service.get_server_config(name)
        if not config:
            return False, f"Server configuration not found: {name}"

        # Check if server is already running
        try:
            status = await self.get_server_status(name)
            if status.state in ("running", "starting"):
                return False, f"Server is already {status.state}"
        except Exception:
            # Server doesn't exist, which is fine for starting
            pass

        return True, ""

    async def cleanup(self) -> None:
        """Cleanup resources when service is shutting down."""
        if self._initialized:
            await self.stop_all_servers()
            self._initialized = False
