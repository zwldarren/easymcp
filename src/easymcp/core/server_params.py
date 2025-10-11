"""Converts API server configurations to MCP client parameters."""

from mcp.client.stdio import StdioServerParameters

from ..models import ServerConfigAPI, SseConfig, StdioConfig, StreamableHttpConfig


def api_config_to_mcp_params(
    config: ServerConfigAPI, extra_env: dict[str, str] | None = None
) -> StdioServerParameters | dict:
    """Converts an API ServerConfig model to MCP client parameters."""
    transport = config.transport

    if isinstance(transport, StdioConfig):
        env = transport.env.copy()
        if extra_env:
            env.update(extra_env)
        return StdioServerParameters(
            command=transport.command,
            args=transport.args,
            env=env,
        )
    elif isinstance(transport, SseConfig):
        return {
            "url": transport.url,
            "headers": transport.headers,
        }
    elif isinstance(transport, StreamableHttpConfig):
        return {
            "url": transport.url,
            "headers": transport.headers,
            "transport": "streamable-http",
            "authorization": transport.authorization,
        }
    else:
        msg = f"Unsupported transport type: {type(transport)}"
        raise ValueError(msg)
