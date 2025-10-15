"""Consolidated configuration service combining core and services functionality."""

import asyncio
import logging
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from easymcp.core.database import get_db_session
from easymcp.core.errors import ConfigurationError
from easymcp.models import GlobalConfig, GlobalConfigAPI, ServerConfig, ServerConfigAPI

logger = logging.getLogger(__name__)


class ConsolidatedConfigService:
    """Consolidated configuration service with memory caching and database persistence."""

    def __init__(self) -> None:
        self._configs: dict[str, ServerConfigAPI] = {}
        self._global_config: GlobalConfigAPI = GlobalConfigAPI()
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service by loading all configurations from database."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:  # Double-check pattern
                return

            try:
                async with get_db_session() as session:
                    self._global_config = await self._get_global_config(session)
                    self._configs = await self._get_all_server_configs(session)
                    self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize ConsolidatedConfigService: {e}")
                raise

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    # Basic access properties
    @property
    def configs(self) -> dict[str, ServerConfigAPI]:
        """Get all server configurations (read-only)."""
        if not self._initialized:
            raise RuntimeError("ConsolidatedConfigService not initialized")
        return self._configs.copy()

    @property
    def global_config(self) -> GlobalConfigAPI:
        """Get global configuration (read-only)."""
        if not self._initialized:
            raise RuntimeError("ConsolidatedConfigService not initialized")
        return self._global_config

    # High-level interface methods (from services layer)
    async def get_all_server_configs(self) -> dict[str, ServerConfigAPI]:
        """Get all server configurations."""
        if not self._initialized:
            await self.initialize()
        return self.configs

    async def get_server_config(self, name: str) -> ServerConfigAPI | None:
        """Get a specific server configuration by name."""
        if not self._initialized:
            await self.initialize()
        return self._configs.get(name)

    async def get_global_config_safe(self) -> GlobalConfigAPI:
        """Get the global configuration."""
        if not self._initialized:
            await self.initialize()
        return self.global_config

    # Configuration update methods
    async def update_server_config(
        self, server_name: str, config: ServerConfigAPI, validate_command: bool = True
    ) -> ServerConfigAPI:
        """Update or create a server configuration."""
        if not self._initialized:
            await self.initialize()

        logger.info(f"Updating server configuration for '{server_name}': {config}")
        return await self._update_server_config_atomic(server_name, config)

    async def update_global_config(self, config: GlobalConfigAPI) -> GlobalConfigAPI:
        """Update the global configuration."""
        if not self._initialized:
            await self.initialize()

        logger.info(f"Updating global configuration: {config}")
        return await self._update_global_config_atomic(config)

    async def delete_server_config(self, name: str) -> None:
        """Delete a server configuration."""
        if not self._initialized:
            await self.initialize()

        logger.info(f"Deleting server configuration: '{name}'")
        await self._delete_server_config_atomic(name)

    async def refresh_configs(self) -> None:
        """Refresh all configurations from database."""
        if not self._initialized:
            await self.initialize()
            return

        logger.info("Refreshing all configurations")
        await self._refresh_all_configs()

    # Utility methods (from services layer)
    async def validate_server_config(self, config: ServerConfigAPI) -> tuple[bool, str]:
        """Validate a server configuration."""
        try:
            # Basic validation is handled by Pydantic models
            # Additional business logic validation can be added here
            return True, ""
        except Exception as e:
            return False, str(e)

    async def export_configs(self) -> dict[str, Any]:
        """Export all configurations for backup."""
        if not self._initialized:
            await self.initialize()

        return {
            "global": await self.get_global_config_safe(),
            "servers": await self.get_all_server_configs(),
        }

    async def import_configs(self, configs: dict[str, Any]) -> None:
        """Import configurations from backup."""
        if not self._initialized:
            await self.initialize()

        # Import global config
        if "global" in configs:
            await self.update_global_config(GlobalConfigAPI.model_validate(configs["global"]))

        # Import server configs
        if "servers" in configs:
            for name, server_config in configs["servers"].items():
                await self.update_server_config(name, ServerConfigAPI.model_validate(server_config))

        logger.info("Successfully imported configurations")

    # Core atomic operations
    async def _update_server_config_atomic(
        self, server_name: str, config: ServerConfigAPI
    ) -> ServerConfigAPI:
        """Update server configuration with guaranteed consistency."""
        async with self._lock:
            try:
                async with get_db_session() as session:
                    updated_config = await self._update_server_config(session, server_name, config)
                    # Update memory cache atomically
                    self._configs[server_name] = updated_config
                    logger.info(f"Server configuration updated for '{server_name}'")
                    return updated_config
            except Exception as e:
                logger.error(f"Failed to update server configuration for '{server_name}': {e}")
                raise ConfigurationError(f"Failed to update server configuration: {e}") from e

    async def _update_global_config_atomic(self, config: GlobalConfigAPI) -> GlobalConfigAPI:
        """Update global configuration with guaranteed consistency."""
        async with self._lock:
            try:
                async with get_db_session() as session:
                    updated_config = await self._update_global_config(session, config)
                    # Update memory cache atomically
                    self._global_config = updated_config
                    logger.info("Global configuration updated")
                    return updated_config
            except Exception as e:
                logger.error(f"Failed to update global configuration: {e}")
                raise ConfigurationError(f"Failed to update global configuration: {e}") from e

    async def _delete_server_config_atomic(self, server_name: str) -> None:
        """Delete server configuration with guaranteed consistency."""
        async with self._lock:
            try:
                async with get_db_session() as session:
                    await self._delete_server_config(session, server_name)
                    # Remove from memory cache atomically
                    if server_name in self._configs:
                        del self._configs[server_name]
                    logger.info(f"Server configuration deleted for '{server_name}'")
            except Exception as e:
                logger.error(f"Failed to delete server configuration for '{server_name}': {e}")
                raise ConfigurationError(f"Failed to delete server configuration: {e}") from e

    async def _refresh_all_configs(self) -> None:
        """Force refresh all configurations from database."""
        async with self._lock:
            try:
                async with get_db_session() as session:
                    self._global_config = await self._get_global_config(session)
                    self._configs = await self._get_all_server_configs(session)
                    logger.info("All configurations refreshed from database")
            except Exception as e:
                logger.error(f"Failed to refresh configurations: {e}")
                raise ConfigurationError(f"Failed to refresh configurations: {e}") from e

    # Database operations
    async def _get_global_config(self, session: AsyncSession) -> GlobalConfigAPI:
        """Retrieve global configuration from the database."""
        stmt = select(GlobalConfig).order_by("id")
        result = await session.exec(stmt)
        config_orm = result.one_or_none()

        if config_orm:
            return GlobalConfigAPI.from_sqlmodel(config_orm)
        else:
            return GlobalConfigAPI()

    async def _update_global_config(
        self, session: AsyncSession, config: GlobalConfigAPI
    ) -> GlobalConfigAPI:
        """Update global configuration in the database."""
        try:
            stmt = select(GlobalConfig).order_by("id")
            result = await session.exec(stmt)
            config_orm = result.one_or_none()

            if not config_orm:
                config_orm = config.to_sqlmodel()
                session.add(config_orm)
            else:
                config_orm.stateless = config.stateless
                config_orm.log_level = config.log_level
                config_orm.pass_environment = config.pass_environment
                config_orm.auth = config.auth

            await session.commit()
            await session.refresh(config_orm)
            logger.debug("Global configuration updated successfully")
            return GlobalConfigAPI.from_sqlmodel(config_orm)
        except Exception as e:
            logger.error(f"Failed to update global configuration: {e}")
            raise

    async def _get_all_server_configs(self, session: AsyncSession) -> dict[str, ServerConfigAPI]:
        """Retrieve all server configurations from the database."""
        result = await session.exec(select(ServerConfig))
        servers = result.all()

        configs = {}
        for server in servers:
            try:
                configs[server.name] = ServerConfigAPI.from_sqlmodel(server)
            except ValueError as e:
                logger.error(f"Error converting server config for '{server.name}': {e}")
        return configs

    async def _update_server_config(
        self, session: AsyncSession, server_name: str, config: ServerConfigAPI
    ) -> ServerConfigAPI:
        """Update a specific server's configuration in the database."""
        try:
            result = await session.exec(
                select(ServerConfig).where(ServerConfig.name == server_name)
            )
            server = result.one_or_none()

            if not server:
                server = config.to_sqlmodel(server_name)
                session.add(server)
            else:
                server.enabled = config.enabled
                server.timeout = config.timeout
                server.transport_type = config.transport.type
                server.transport_config = config.transport.model_dump(exclude={"type"})

                # Handle auth config for streamable-http
                if config.transport.type == "streamable-http" and config.transport.authorization:
                    auth = config.transport.authorization.grant
                    server.auth_config = {
                        "grant_type": auth.grant_type,
                        "token_url": auth.token_url,
                        "client_id": auth.client_id,
                        "client_secret": auth.client_secret,
                        "scope": auth.scope,
                    }
                else:
                    server.auth_config = None

            await session.commit()
            await session.refresh(server)
            logger.debug(f"Server configuration updated successfully for '{server_name}'")
            return ServerConfigAPI.from_sqlmodel(server)
        except Exception as e:
            logger.error(f"Failed to update server configuration for '{server_name}': {e}")
            raise

    async def _delete_server_config(self, session: AsyncSession, server_name: str) -> None:
        """Delete a specific server's configuration from the database."""
        try:
            stmt = select(ServerConfig).where(ServerConfig.name == server_name)
            result = await session.exec(stmt)
            server = result.one_or_none()

            if not server:
                raise ConfigurationError(f"Server '{server_name}' not found")

            await session.delete(server)
            await session.commit()
            logger.debug(f"Server configuration deleted successfully for '{server_name}'")
        except Exception as e:
            logger.error(f"Failed to delete server configuration for '{server_name}': {e}")
            raise


# Global singleton instance
_consolidated_config_service = None


def get_consolidated_config_service() -> ConsolidatedConfigService:
    """Get the singleton instance of ConsolidatedConfigService."""
    global _consolidated_config_service
    if _consolidated_config_service is None:
        _consolidated_config_service = ConsolidatedConfigService()
    return _consolidated_config_service


# FastAPI dependency
async def get_config_service() -> ConsolidatedConfigService:
    """Get a configuration service instance."""
    service = get_consolidated_config_service()
    await service.initialize()
    return service
