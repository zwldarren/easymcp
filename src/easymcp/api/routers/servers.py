"""API routes for managing servers."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ...models import (
    ServerStatus,
    StartServerRequest,
)
from ..auth import get_current_user
from ..dependencies import AppStateDep, require_scope_dependency

router = APIRouter()


@router.get(
    "/",
    response_model=dict[str, Any],
    summary="List all servers",
    description="Retrieves a list of all configured servers with their current status "
    "and configuration details.",
    responses={
        200: {"description": "Successfully retrieved server list"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        503: {"description": "Server manager not initialized"},
    },
    dependencies=[Depends(require_scope_dependency("read:servers"))],
)
async def list_servers(
    app_state: AppStateDep,
    _: str = Depends(get_current_user),  # Authentication required
) -> dict[str, Any]:
    if not app_state.server_manager:
        raise HTTPException(status_code=503, detail="Server manager not initialized")

    server_statuses = app_state.get_all_servers_status()

    # Get server configurations from the unified service
    server_configs = app_state.server_manager.configs

    servers = {}
    for server_name, status in server_statuses.items():
        if server_name in server_configs:
            servers[server_name] = {
                "name": server_name,
                "config": server_configs[server_name].model_dump(),
                "status": status.model_dump(),
            }

    return {"servers": servers}


@router.get(
    "/{server_name}/status",
    response_model=ServerStatus,
    summary="Get server status",
    description="Retrieves the current status of a specific MCP server including its state, "
    "endpoints, and capabilities.",
    responses={
        200: {"description": "Successfully retrieved server status"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Server not found"},
    },
    dependencies=[Depends(require_scope_dependency("read:servers"))],
)
async def get_server_status(
    server_name: str,
    app_state: AppStateDep,
    _: str = Depends(get_current_user),  # Authentication required
) -> ServerStatus:
    try:
        return app_state.get_server_status(server_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post(
    "/{server_name}/start",
    response_model=ServerStatus,
    summary="Start a server",
    description="Starts a specific MCP server with the provided configuration options.",
    responses={
        200: {"description": "Server started successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Server already running"},
        500: {"description": "Failed to start server"},
    },
    dependencies=[Depends(require_scope_dependency("write:servers"))],
)
async def start_server(
    server_name: str,
    request: StartServerRequest,
    app_state: AppStateDep,
    http_request: Request,
    _: str = Depends(get_current_user),  # Authentication required
) -> ServerStatus:
    # Check if authenticated via API key and deny access
    if (
        hasattr(http_request.state, "auth_info")
        and http_request.state.auth_info.get("type") == "api_key"
    ):
        raise HTTPException(status_code=403, detail="API keys cannot start servers")

    try:
        return await app_state.start_server(server_name, request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start server: {e}") from e


@router.post(
    "/{server_name}/stop",
    response_model=ServerStatus,
    summary="Stop a server",
    description="Stops a specific MCP server that is currently running.",
    responses={
        200: {"description": "Server stopped successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions - API keys cannot stop servers"},
        404: {"description": "Server not running"},
        500: {"description": "Failed to stop server"},
    },
    dependencies=[Depends(require_scope_dependency("write:servers"))],
)
async def stop_server(
    server_name: str,
    app_state: AppStateDep,
    http_request: Request,
    _: str = Depends(get_current_user),  # Authentication required
) -> ServerStatus:
    # Check if authenticated via API key and deny access
    if (
        hasattr(http_request.state, "auth_info")
        and http_request.state.auth_info.get("type") == "api_key"
    ):
        raise HTTPException(status_code=403, detail="API keys cannot stop servers")

    try:
        return await app_state.stop_server(server_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {e}") from e


@router.get(
    "/{server_name}/mcp",
    response_model=dict,
    summary="Get MCP server details",
    description="Retrieves detailed information about a specific MCP server, "
    "including its capabilities and endpoints.",
    responses={
        200: {"description": "Successfully retrieved MCP server details"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Server not found"},
    },
    dependencies=[Depends(require_scope_dependency("read:servers"))],
)
async def get_mcp_server_details(
    server_name: str,
    app_state: AppStateDep,
    _: str = Depends(get_current_user),
) -> dict:
    """Get MCP server details including capabilities and endpoints."""
    try:
        status = app_state.get_server_status(server_name)
        return {
            "server_name": server_name,
            "status": status.model_dump(),
            "capabilities": status.capabilities,
            "endpoints": status.endpoints,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
