"""Manages the state of the EasyMCP application."""

import asyncio
import logging
import time
import typing as t
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import APIRouter

from .config import get_settings
from .core.server_manager import ServerManager
from .models import (
    GlobalConfigAPI,
    ServerStatus,
    StartServerRequest,
)


class AppState:
    """Manages the state of the EasyMCP application."""

    def __init__(self) -> None:
        """Initializes the application state."""
        self._server_manager: ServerManager | None = None
        self._initialized = False

        self.global_config = GlobalConfigAPI(auth={})
        self.start_time = time.time()
        self.api_last_activity = datetime.now(UTC)
        settings_obj = get_settings()
        self.host: str = settings_obj.host
        self.port: int = settings_obj.port
        self.shutdown_event = asyncio.Event()

        # API request metrics
        self.request_total: int = 0
        self.request_successful: int = 0
        self.request_failed: int = 0

    def initialize_services(self, router: APIRouter) -> None:
        """Initialize services that depend on the FastAPI app instance."""
        if self._server_manager is not None:
            return  # Already initialized
        self._server_manager = ServerManager(router, self.shutdown_event)

    async def initialize(self) -> None:
        """Initializes the application state asynchronously."""
        if self._initialized:
            return  # Already initialized

        if not self._server_manager:
            raise RuntimeError("Server manager not initialized. Call initialize_services first.")

        # Initialize the server manager with unified configuration service
        await self._server_manager.initialize()

        # Load global config from the unified service
        self.global_config = self._server_manager.global_config

        self._initialized = True
        logging.info("Application state initialized with unified configuration service.")

    @property
    def server_manager(self) -> ServerManager:
        """Get the server manager, ensuring it's initialized."""
        if not self._server_manager:
            raise RuntimeError("Server manager not initialized.")
        return self._server_manager

    # --- Delegated methods to ServerManager ---
    @property
    def running_servers(self) -> dict[str, t.Any]:
        """Get the currently running server instances."""
        return self.server_manager.servers

    def get_server_status(self, name: str) -> ServerStatus:
        """Gets the status of a server."""
        return self.server_manager.get_server_status(name)

    def get_all_servers_status(self) -> dict[str, ServerStatus]:
        """Gets the status of all servers."""
        return self.server_manager.get_all_servers_status()

    async def start_server(
        self,
        name: str,
        request: StartServerRequest,
    ) -> ServerStatus:
        """Starts a configured server."""
        return await self.server_manager.start_server(name, request)

    async def stop_server(self, name: str) -> ServerStatus:
        """Stops a configured server."""
        return await self.server_manager.stop_server(name)

    @asynccontextmanager
    async def lifespan(self) -> t.AsyncIterator[None]:
        """Context manager for application lifespan."""
        try:
            yield
        finally:
            # Cleanup on shutdown
            if self._server_manager:
                await self._server_manager.close()


# Singleton instance of the application state
app_state = AppState()
