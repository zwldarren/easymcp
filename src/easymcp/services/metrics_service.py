"""Metrics service for collecting and managing application metrics.

This service provides a centralized way to collect, store, and retrieve
various application metrics including performance, usage, and system statistics.
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from ..core.performance_monitor import get_performance_monitor
from ..models import (
    McpStatistics,
    ServerCallCounts,
    ServerStatistics,
    SystemMetrics,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for managing application metrics and statistics."""

    def __init__(self):
        """Initialize the metrics service."""
        self._performance_monitor = get_performance_monitor()
        self._initialized = False

        # Custom metrics storage
        self._request_metrics: dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "requests_per_minute": [],
            "last_minute_requests": 0,
        }

        self._server_metrics: dict[str, dict[str, Any]] = {}
        self._start_time = time.time()

    async def initialize(self) -> None:
        """Initialize the metrics service."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("Metrics service initialized")

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized

    # Request Metrics
    def record_request(self, success: bool = True, response_time: float | None = None) -> None:
        """Record a request metric.

        Args:
            success: Whether the request was successful
            response_time: Response time in seconds
        """
        if not self._initialized:
            return

        self._request_metrics["total_requests"] += 1

        if success:
            self._request_metrics["successful_requests"] += 1
        else:
            self._request_metrics["failed_requests"] += 1

        if response_time is not None:
            self._performance_monitor.record_request_time(response_time)

        # Update per-minute metrics
        current_time = time.time()
        self._request_metrics["last_minute_requests"] += 1

        # Clean old entries (older than 1 hour)
        cutoff_time = current_time - 3600
        self._request_metrics["requests_per_minute"] = [
            (timestamp, count)
            for timestamp, count in self._request_metrics["requests_per_minute"]
            if timestamp > cutoff_time
        ]

    def get_request_metrics(self) -> dict[str, Any]:
        """Get request metrics.

        Returns:
            Dictionary containing request metrics
        """
        if not self._initialized:
            return {}

        return {
            **self._request_metrics,
            "success_rate": (
                self._request_metrics["successful_requests"]
                / max(self._request_metrics["total_requests"], 1)
                * 100
            ),
            "average_requests_per_minute": self._calculate_average_requests_per_minute(),
        }

    def _calculate_average_requests_per_minute(self) -> float:
        """Calculate average requests per minute over the last hour."""
        if not self._request_metrics["requests_per_minute"]:
            return 0.0

        total_requests = sum(count for _, count in self._request_metrics["requests_per_minute"])
        return total_requests / len(self._request_metrics["requests_per_minute"])

    # Server Metrics
    def record_server_call(self, server_name: str, call_type: str) -> None:
        """Record a server call.

        Args:
            server_name: Name of the server
            call_type: Type of call (tools, prompts, resources, etc.)
        """
        if not self._initialized:
            return

        if server_name not in self._server_metrics:
            self._server_metrics[server_name] = {
                "call_counts": ServerCallCounts().model_dump(),
                "active_connections": 0,
                "last_activity": datetime.now(UTC).isoformat(),
                "uptime_start": time.time(),
            }

        # Update call counts
        call_counts = self._server_metrics[server_name]["call_counts"]
        if call_type in call_counts:
            call_counts[call_type] += 1

        # Update last activity
        self._server_metrics[server_name]["last_activity"] = datetime.now(UTC).isoformat()

    def record_server_connection(self, server_name: str, connected: bool) -> None:
        """Record a server connection change.

        Args:
            server_name: Name of the server
            connected: Whether the server is now connected
        """
        if not self._initialized:
            return

        if server_name not in self._server_metrics:
            self._server_metrics[server_name] = {
                "call_counts": ServerCallCounts().model_dump(),
                "active_connections": 0,
                "last_activity": datetime.now(UTC).isoformat(),
                "uptime_start": time.time(),
            }

        if connected:
            self._server_metrics[server_name]["active_connections"] += 1
        else:
            self._server_metrics[server_name]["active_connections"] = max(
                0, self._server_metrics[server_name]["active_connections"] - 1
            )

    def get_server_metrics(self, server_name: str) -> dict[str, Any] | None:
        """Get metrics for a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Server metrics or None if not found
        """
        if not self._initialized:
            return None

        if server_name not in self._server_metrics:
            return None

        metrics = self._server_metrics[server_name].copy()

        # Calculate uptime
        if "uptime_start" in metrics:
            metrics["uptime_seconds"] = time.time() - metrics["uptime_start"]

        return metrics

    def get_all_server_metrics(self) -> dict[str, dict[str, Any]]:
        """Get metrics for all servers.

        Returns:
            Dictionary mapping server names to their metrics
        """
        if not self._initialized:
            return {}

        result = {}
        for server_name, _metrics in self._server_metrics.items():
            result[server_name] = self.get_server_metrics(server_name) or {}

        return result

    # System Metrics
    def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system metrics.

        Returns:
            System metrics object
        """
        if not self._initialized:
            return SystemMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                servers={},
                requests={},
            )

        # Get performance metrics
        perf_metrics = self._performance_monitor.get_metrics()

        # Get server metrics
        server_metrics = self.get_all_server_metrics()

        # Calculate total calls
        total_calls = {"tools": 0, "prompts": 0, "resources": 0}
        total_connections = 0

        for metrics in server_metrics.values():
            call_counts = metrics.get("call_counts", {})
            total_calls["tools"] += call_counts.get("tools", 0)
            total_calls["prompts"] += call_counts.get("prompts", 0)
            total_calls["resources"] += call_counts.get("resources", 0)
            total_connections += metrics.get("active_connections", 0)

        return SystemMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            servers={name: 1 for name in server_metrics},
            requests={
                "total": self._request_metrics["total_requests"],
                "successful": self._request_metrics["successful_requests"],
                "failed": self._request_metrics["failed_requests"],
            },
            performance={
                "average_response_time": perf_metrics.get("average_response_time", 0),
                "last_response_time": perf_metrics.get("last_response_time", 0),
                "cpu_usage": perf_metrics.get("cpu_usage", 0),
                "memory_usage": perf_metrics.get("memory_usage", {}),
            },
            environment=perf_metrics.get("environment", {}),
        )

    def get_mcp_statistics(self) -> McpStatistics:
        """Get MCP-specific statistics.

        Returns:
            MCP statistics object
        """
        if not self._initialized:
            return McpStatistics(
                timestamp=datetime.now(UTC).isoformat(),
                servers={},
                total_active_connections=0,
            )

        server_metrics = self.get_all_server_metrics()
        servers = {}
        total_connections = 0
        total_calls = {"tools": 0, "prompts": 0, "resources": 0}

        for server_name, metrics in server_metrics.items():
            call_counts = metrics.get("call_counts", {})
            server_stats = ServerStatistics(
                name=server_name,
                status="running",  # This would need to be determined from actual server status
                call_counts=ServerCallCounts(**call_counts),
                active_connections=metrics.get("active_connections", 0),
                uptime_seconds=metrics.get("uptime_seconds", 0),
                last_activity=metrics.get("last_activity", ""),
            )
            servers[server_name] = server_stats

            total_connections += server_stats.active_connections
            total_calls["tools"] += server_stats.call_counts.tools
            total_calls["prompts"] += server_stats.call_counts.prompts
            total_calls["resources"] += server_stats.call_counts.resources

        return McpStatistics(
            timestamp=datetime.now(UTC).isoformat(),
            servers=servers,
            total_active_connections=total_connections,
            total_calls=total_calls,
        )

    # Utility Methods
    def get_uptime_seconds(self) -> float:
        """Get the uptime of the metrics service.

        Returns:
            Uptime in seconds
        """
        return time.time() - self._start_time

    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)."""
        if not self._initialized:
            return

        self._request_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "requests_per_minute": [],
            "last_minute_requests": 0,
        }
        self._server_metrics.clear()
        self._start_time = time.time()

        logger.info("Metrics reset")

    async def cleanup(self) -> None:
        """Cleanup resources when service is shutting down."""
        if self._initialized:
            logger.info("Cleaning up metrics service")
            self._initialized = False


# Dependency function for FastAPI
async def get_metrics_service() -> MetricsService:
    """Get a metrics service instance."""
    service = MetricsService()
    await service.initialize()
    return service
