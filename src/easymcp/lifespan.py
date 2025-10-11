"""Manages the application's lifespan events."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from .core.database import init_db
from .models import StartServerRequest
from .state import app_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logging.info("EasyMCP API starting up...")

    # Initialize database
    await init_db()

    # Initialize services
    app.state.app_state = app_state
    app_state.initialize_services(app.router)
    await app_state.initialize()
    # Auto-start all enabled servers with comprehensive error handling
    auto_start_success_count = 0
    auto_start_failure_count = 0
    auto_start_errors: list[dict[str, Any]] = []

    logging.info("Starting auto-start process for enabled servers...")

    try:
        # Get server configurations
        server_configs = app_state.server_manager.configs
        start_request = StartServerRequest(stateless=app_state.global_config.stateless)

        enabled_servers = [name for name, config in server_configs.items() if config.enabled]

        if not enabled_servers:
            logging.info("No enabled servers found for auto-start")
        else:
            server_list = ", ".join(enabled_servers)
            logging.info(
                f"Found {len(enabled_servers)} enabled servers for auto-start: {server_list}"
            )

            # Auto-start each enabled server with individual error handling
            for server_name in enabled_servers:
                config = server_configs[server_name]
                # Get command info based on transport type
                if config.transport.type == "stdio":
                    command_preview = config.transport.command[:50] + (
                        "..." if len(config.transport.command) > 50 else ""
                    )
                    transport_info = f"command: {command_preview}"
                elif config.transport.type in ["sse", "streamable-http"]:
                    url_preview = config.transport.url[:50]
                    if len(config.transport.url) > 50:
                        url_preview += "..."
                    transport_info = f"url: {url_preview}"
                else:
                    transport_info = f"type: {config.transport.type}"

                logging.info(f"Auto-starting server: {server_name} ({transport_info})")

                try:
                    # Add timeout for server startup to prevent hanging
                    await asyncio.wait_for(
                        app_state.start_server(server_name, start_request),
                        timeout=30.0,  # 30 second timeout for each server
                    )
                    auto_start_success_count += 1
                    logging.info(f"Successfully auto-started server: {server_name}")

                except TimeoutError:
                    auto_start_failure_count += 1
                    error_msg = f"Server '{server_name}' timed out during startup (30s limit)"
                    auto_start_errors.append(
                        {"server": server_name, "error": error_msg, "type": "timeout"}
                    )
                    logging.error(f"Auto-start timeout for server '{server_name}': {error_msg}")

                except Exception as e:
                    auto_start_failure_count += 1
                    error_type = type(e).__name__
                    error_msg = str(e)
                    # Get transport details for error reporting
                    if config.transport.type == "stdio":
                        transport_details: dict[str, Any] = {
                            "type": "stdio",
                            "command": config.transport.command,
                            "args": config.transport.args,
                            "env": config.transport.env,
                        }
                    elif config.transport.type == "sse":
                        transport_details = {
                            "type": "sse",
                            "url": config.transport.url,
                            "headers": config.transport.headers,
                        }
                    elif config.transport.type == "streamable-http":
                        transport_details = {
                            "type": "streamable-http",
                            "url": config.transport.url,
                            "headers": config.transport.headers,
                            "authorization": "enabled"
                            if config.transport.authorization is not None
                            else "disabled",
                        }
                    else:
                        transport_details = {"type": config.transport.type}

                    auto_start_errors.append(
                        {
                            "server": server_name,
                            "error": error_msg,
                            "type": error_type,
                            "details": transport_details,
                        }
                    )
                    logging.error(
                        f"Failed to auto-start server '{server_name}': {error_type}: {error_msg}"
                    )

                    # Log full exception for debugging
                    logging.debug(
                        f"Full exception details for server '{server_name}':", exc_info=True
                    )

    except Exception as e:
        # This handles errors in the auto-start process itself (not individual server errors)
        error_type = type(e).__name__
        error_msg = str(e)
        logging.critical(f"Critical error during auto-start process: {error_type}: {error_msg}")
        logging.debug("Auto-start process exception details:", exc_info=True)

        # Continue application startup even if auto-start fails completely
        logging.warning("Continuing application startup despite auto-start process failure")

    # Log auto-start summary
    total_enabled = 0
    if "enabled_servers" in locals():
        total_enabled = len(locals()["enabled_servers"])
    logging.info(
        f"Auto-start process completed: {auto_start_success_count}/{total_enabled} "
        f"servers started successfully"
    )

    if auto_start_failure_count > 0:
        logging.warning(f"Auto-start failures: {auto_start_failure_count} servers failed to start")
        for error in auto_start_errors:
            logging.warning(f"  - {error['server']}: {error['type']} - {error['error']}")

    logging.info("EasyMCP API startup complete")

    async with app_state.lifespan():
        yield
        logging.info("EasyMCP API shutting down...")

        # Signal all SSE connections to stop
        if app_state.shutdown_event:
            app_state.shutdown_event.set()

        # Clean up global server data to prevent memory leaks
        try:
            from .mcp_stack.server import cleanup_all_server_data

            await cleanup_all_server_data()
        except Exception as e:
            logging.warning(f"Error during server data cleanup: {e}")

        logging.info("EasyMCP API shutdown complete")
