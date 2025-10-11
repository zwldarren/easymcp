"""Simplified capability handlers for the MCP proxy server.

This module provides direct registration of MCP capability handlers
without abstract base classes or factory patterns.
"""

import logging
import typing as t

from mcp import server, types
from mcp.client.session import ClientSession

logger = logging.getLogger(__name__)


def register_capabilities(
    app: server.Server[object],
    remote_app: ClientSession,
    capabilities: types.ServerCapabilities,
    *,
    record_call: t.Callable[[str], None] | None = None,
) -> None:
    """Register MCP capability handlers directly."""

    # Register tools capability
    if capabilities.tools:

        async def list_tools_handler(_: t.Any) -> types.ServerResult:
            result = await remote_app.list_tools()
            return types.ServerResult(root=result)

        async def call_tool_handler(req: types.CallToolRequest) -> types.ServerResult:
            # Record tool call for statistics
            if record_call:
                record_call("tools")

            try:
                result = await remote_app.call_tool(req.params.name, req.params.arguments or {})
                return types.ServerResult(root=result)
            except Exception as e:
                return types.ServerResult(
                    root=types.CallToolResult(
                        content=[types.TextContent(type="text", text=str(e))],
                        isError=True,
                    ),
                )

        app.request_handlers[types.ListToolsRequest] = list_tools_handler
        app.request_handlers[types.CallToolRequest] = call_tool_handler
        logger.debug("Tools capability registered")

    # Register prompts capability
    if capabilities.prompts:

        async def list_prompts_handler(_: t.Any) -> types.ServerResult:
            result = await remote_app.list_prompts()
            return types.ServerResult(root=result)

        async def get_prompt_handler(req: types.GetPromptRequest) -> types.ServerResult:
            # Record prompt call for statistics
            if record_call:
                record_call("prompts")

            result = await remote_app.get_prompt(req.params.name, req.params.arguments)
            return types.ServerResult(root=result)

        app.request_handlers[types.ListPromptsRequest] = list_prompts_handler
        app.request_handlers[types.GetPromptRequest] = get_prompt_handler
        logger.debug("Prompts capability registered")

    # Register resources capability
    if capabilities.resources:

        async def list_resources_handler(_: t.Any) -> types.ServerResult:
            result = await remote_app.list_resources()
            return types.ServerResult(root=result)

        async def list_resource_templates_handler(_: t.Any) -> types.ServerResult:
            result = await remote_app.list_resource_templates()
            return types.ServerResult(root=result)

        async def read_resource_handler(req: types.ReadResourceRequest) -> types.ServerResult:
            # Record resource call for statistics
            if record_call:
                record_call("resources")

            result = await remote_app.read_resource(req.params.uri)
            return types.ServerResult(root=result)

        async def subscribe_resource_handler(req: types.SubscribeRequest) -> types.ServerResult:
            await remote_app.subscribe_resource(req.params.uri)
            return types.ServerResult(root=types.EmptyResult())

        async def unsubscribe_resource_handler(req: types.UnsubscribeRequest) -> types.ServerResult:
            await remote_app.unsubscribe_resource(req.params.uri)
            return types.ServerResult(root=types.EmptyResult())

        app.request_handlers[types.ListResourcesRequest] = list_resources_handler
        app.request_handlers[types.ListResourceTemplatesRequest] = list_resource_templates_handler
        app.request_handlers[types.ReadResourceRequest] = read_resource_handler
        app.request_handlers[types.SubscribeRequest] = subscribe_resource_handler
        app.request_handlers[types.UnsubscribeRequest] = unsubscribe_resource_handler
        logger.debug("Resources capability registered")

    # Register progress notifications (always available)
    async def send_progress_notification_handler(req: types.ProgressNotification) -> None:
        await remote_app.send_progress_notification(
            req.params.progressToken,
            req.params.progress,
            req.params.total,
            req.params.message,
        )

    app.notification_handlers[types.ProgressNotification] = send_progress_notification_handler
    logger.debug("Progress notifications registered")

    # Register completions capability (always available)
    async def complete_handler(req: types.CompleteRequest) -> types.ServerResult:
        result = await remote_app.complete(
            req.params.ref,
            req.params.argument.model_dump(),
        )
        return types.ServerResult(root=result)

    app.request_handlers[types.CompleteRequest] = complete_handler
    logger.debug("Completions capability registered")
