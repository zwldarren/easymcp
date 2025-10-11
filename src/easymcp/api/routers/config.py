"""API routes for managing configuration."""

from fastapi import APIRouter, HTTPException

from easymcp.services.config_service import get_config_service

from ...models import GlobalConfigAPI, ServerConfigAPI
from ..dependencies import ServerManagerDep

router = APIRouter()


@router.get(
    "/global",
    response_model=GlobalConfigAPI,
    summary="Get global configuration",
    description="Retrieves the current global configuration for the EasyMCP application.",
    responses={200: {"description": "Successfully retrieved global configuration"}},
)
async def get_global_config(server_manager: ServerManagerDep) -> GlobalConfigAPI:
    return server_manager.global_config


@router.get(
    "/servers",
    response_model=dict[str, ServerConfigAPI],
    summary="Get all server configurations",
    description="Retrieves configurations for all MCP servers.",
    responses={200: {"description": "Successfully retrieved server configurations"}},
)
async def get_servers_config(
    server_manager: ServerManagerDep,
) -> dict[str, ServerConfigAPI]:
    return server_manager.configs


@router.put(
    "/servers/{server_name}",
    response_model=ServerConfigAPI,
    summary="Update server configuration",
    description="Updates the configuration for a specific MCP server.",
    responses={
        200: {"description": "Configuration updated successfully"},
        404: {"description": "Server not found"},
    },
)
async def update_server_config(
    server_name: str,
    config: ServerConfigAPI,
) -> ServerConfigAPI:
    """Update server configuration."""
    config_service = await get_config_service()
    updated_config = await config_service.update_server_config(server_name, config)
    if not updated_config:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
    return updated_config


@router.delete(
    "/servers/{server_name}",
    status_code=204,
    summary="Delete server configuration",
    description="Deletes the configuration for a specific MCP server.",
    responses={
        204: {"description": "Configuration deleted successfully"},
        404: {"description": "Server not found"},
    },
)
async def delete_server_config(
    server_name: str,
) -> None:
    """Delete server configuration."""
    config_service = await get_config_service()
    await config_service.delete_server_config(server_name)
