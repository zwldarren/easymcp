"""Create an MCP server that proxies requests through an MCP client.

This server is created independent of any transport mechanism.
"""

import logging
import typing as t

from mcp import server
from mcp.client.session import ClientSession

from .capability_handlers import register_capabilities

logger = logging.getLogger(__name__)


async def create_proxy_server(
    remote_app: ClientSession,
    *,
    record_call: t.Callable[[str], None] | None = None,
) -> server.Server[object]:
    """Create a server instance from a remote app."""
    logger.debug("Sending initialization request to remote MCP server...")
    response = await remote_app.initialize()
    capabilities = response.capabilities

    logger.debug("Configuring proxied MCP server...")
    app: server.Server[object] = server.Server(name=response.serverInfo.name)

    # Register capability handlers based on remote server capabilities
    register_capabilities(
        app,
        remote_app,
        capabilities,
        record_call=record_call,
    )

    return app
