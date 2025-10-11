"""API routes for system status and health checks."""

import logging
import time
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version

from fastapi import APIRouter, Request

from ...core.performance_monitor import get_performance_monitor
from ...models import (
    HealthStatus,
    McpStatistics,
    ServerCallCounts,
    ServerStatistics,
    SystemMetrics,
    SystemStatus,
)
from ..dependencies import AppStateDep

logger = logging.getLogger(__name__)
router = APIRouter()

# Global performance monitor instance
performance_monitor = get_performance_monitor()


@router.get("/")
async def get_system_status(app_state: AppStateDep) -> SystemStatus:
    """Get overall system status."""
    try:
        pkg_version = version("EasyMCP")
    except PackageNotFoundError:
        pkg_version = "unknown"

    server_instances = {
        name: status.state for name, status in app_state.get_all_servers_status().items()
    }

    # Calculate uptime in seconds
    uptime = time.time() - app_state.start_time

    return SystemStatus(
        version=pkg_version,
        api_last_activity=app_state.api_last_activity.isoformat(),
        server_instances=server_instances,
        uptime=uptime,
    )


def _check_component_health(
    running_components: dict,
) -> tuple[str, int]:
    """Check the health of a component (server or client)."""
    issues = sum(1 for component in running_components.values() if component.status == "error")
    if issues > 0:
        if issues == len(running_components):
            return "unhealthy", issues
        return "degraded", issues
    return "healthy", 0


@router.get("/health")
async def get_health_status(
    app_state: AppStateDep,
) -> HealthStatus:
    """Health check endpoint."""
    timestamp = datetime.now(UTC).isoformat()
    checks = {}
    overall_status = "healthy"

    # Check servers health
    servers_status, server_issues = _check_component_health(app_state.running_servers)
    checks["servers"] = servers_status
    if server_issues > 0:
        overall_status = "degraded" if servers_status == "degraded" else "unhealthy"

    # Check configuration persistence by trying to get configs
    try:
        if app_state.server_manager:
            # Access the configs property to verify configuration persistence
            _ = app_state.server_manager.configs
            checks["config"] = "healthy"
        else:
            checks["config"] = "unhealthy"
            overall_status = "degraded"
    except Exception as e:
        logger.warning(f"Configuration health check failed: {e}")
        checks["config"] = "unhealthy"
        overall_status = "degraded"

    return HealthStatus(status=overall_status, timestamp=timestamp, checks=checks)


@router.get("/metrics")
async def get_system_metrics(app_state: AppStateDep, request: Request) -> SystemMetrics:
    """System metrics and performance data."""
    timestamp = datetime.now(UTC).isoformat()

    # Collect server metrics
    servers = {}
    for name, server in app_state.running_servers.items():
        servers[name] = 1 if server.status == "running" else 0

    # Collect request metrics from app_state
    requests = {
        "total": app_state.request_total,
        "successful": app_state.request_successful,
        "failed": app_state.request_failed,
    }

    # Get performance metrics
    performance_metrics = performance_monitor.get_metrics()

    return SystemMetrics(
        timestamp=timestamp,
        servers=servers,
        requests=requests,
        performance=performance_metrics["performance"],
        environment=performance_metrics["environment"],
    )


@router.get("/mcp-statistics")
async def get_mcp_statistics(app_state: AppStateDep) -> McpStatistics:
    """Get MCP server statistics including call counts and active connections."""
    timestamp = datetime.now(UTC).isoformat()

    if not app_state.server_manager:
        return McpStatistics(
            timestamp=timestamp,
            servers={},
            total_active_connections=0,
            total_calls={"tools": 0, "prompts": 0, "resources": 0},
        )

    # Get statistics for all servers
    server_stats_dict = app_state.server_manager.get_all_servers_statistics()

    # Convert to proper model objects
    servers = {}
    total_active_connections = 0
    total_calls = {"tools": 0, "prompts": 0, "resources": 0}

    for server_name, stats_dict in server_stats_dict.items():
        call_counts = ServerCallCounts(**stats_dict["call_counts"])

        server_stat = ServerStatistics(
            name=server_name,
            status=stats_dict["status"],
            call_counts=call_counts,
            active_connections=stats_dict["active_connections"],
            uptime_seconds=stats_dict["uptime_seconds"],
            last_activity=stats_dict["last_activity"],
        )

        servers[server_name] = server_stat

        # Aggregate totals
        total_active_connections += server_stat.active_connections
        total_calls["tools"] += call_counts.tools
        total_calls["prompts"] += call_counts.prompts
        total_calls["resources"] += call_counts.resources

    return McpStatistics(
        timestamp=timestamp,
        servers=servers,
        total_active_connections=total_active_connections,
        total_calls=total_calls,
    )
