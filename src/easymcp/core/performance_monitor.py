"""Performance monitoring utilities for collecting system metrics."""

import os
import platform
import time
import typing as t

import psutil


class PerformanceMonitor:
    """Monitor system performance metrics."""

    def __init__(self) -> None:
        self._start_time = time.time()
        self._last_request_time = 0.0
        self._request_times: list[float] = []
        self._max_request_history = 100  # Keep last 100 request times

    def record_request_time(self, request_time: float) -> None:
        """Record a request response time."""
        self._last_request_time = request_time
        self._request_times.append(request_time)
        # Keep only the last N request times
        if len(self._request_times) > self._max_request_history:
            self._request_times = self._request_times[-self._max_request_history :]

    def get_average_response_time(self) -> float:
        """Calculate average response time in milliseconds."""
        if not self._request_times:
            return 0.0
        return (sum(self._request_times) / len(self._request_times)) * 1000  # Convert to ms

    def get_last_response_time(self) -> float:
        """Get the last response time in milliseconds."""
        return self._last_request_time * 1000  # Convert to ms

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    def get_memory_usage(self) -> dict[str, float]:
        """Get memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                "used": memory_info.rss / 1024 / 1024,  # MB
                "percent": process.memory_percent(),
            }
        except Exception:
            return {"used": 0.0, "percent": 0.0}

    def get_environment_info(self) -> dict[str, str]:
        """Get system environment information."""
        return {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "environment": os.getenv("EASYMCP_ENVIRONMENT", "development"),
            "hostname": platform.node(),
        }

    def get_metrics(self) -> dict[str, t.Any]:
        """Get all performance metrics."""
        memory_info = self.get_memory_usage()

        return {
            "performance": {
                "cpu_usage_percent": self.get_cpu_usage(),
                "memory_used_mb": memory_info["used"],
                "memory_usage_percent": memory_info["percent"],
                "average_response_time_ms": self.get_average_response_time(),
                "last_response_time_ms": self.get_last_response_time(),
                "uptime_seconds": time.time() - self._start_time,
            },
            "environment": self.get_environment_info(),
        }


# Singleton instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the singleton performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
