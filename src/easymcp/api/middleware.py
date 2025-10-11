"""Middleware for the EasyMCP API."""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

# Global performance monitor instance
performance_monitor = get_performance_monitor()


class MiddlewarePriority(Enum):
    """Priority levels for middleware execution order."""

    HIGHEST = 1000
    SECURITY = 900
    AUTHENTICATION = 800
    AUDIT = 700
    RATE_LIMIT = 600
    BUSINESS_LOGIC = 500
    METRICS = 400
    LOWEST = 100


@dataclass
class MiddlewareContext:
    """Context object passed between middleware components."""

    request_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    start_time: float = field(default_factory=time.time)

    # Authentication info
    username: str | None = None
    auth_type: str | None = None
    auth_scopes: list[str] = field(default_factory=list)

    # Request metadata
    client_ip: str | None = None
    user_agent: str | None = None

    # Custom data storage for middleware
    data: dict[str, Any] = field(default_factory=dict)

    # Audit fields
    should_audit: bool = True
    audit_level: str = "INFO"

    # Rate limiting fields
    rate_limit_key: str | None = None
    rate_limit_remaining: int | None = None

    @property
    def response_time(self) -> float:
        """Calculate response time in seconds."""
        return time.time() - self.start_time


class EasyMCPMiddleware(BaseHTTPMiddleware, ABC):
    """Base class for all EasyMCP middleware components."""

    def __init__(self, app, priority: MiddlewarePriority = MiddlewarePriority.BUSINESS_LOGIC):
        super().__init__(app)
        self.priority = priority
        self.logger = logging.getLogger(f"easymcp.middleware.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the middleware."""
        pass

    def _get_context(self, request: Request) -> MiddlewareContext:
        """Get or create middleware context for the request."""
        if not hasattr(request.state, "middleware_context"):
            # Generate a unique request ID
            import uuid

            request_id = str(uuid.uuid4())

            # Get client info
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")

            context = MiddlewareContext(
                request_id=request_id, client_ip=client_ip, user_agent=user_agent
            )
            request.state.middleware_context = context

        return request.state.middleware_context

    async def pre_process(self, request: Request, context: MiddlewareContext) -> Response | None:
        """Hook called before the request is processed.

        Return a Response to short-circuit the request chain, or None to continue.
        """
        return None

    async def post_process(
        self, request: Request, response: Response, context: MiddlewareContext
    ) -> Response:
        """Hook called after the request is processed.

        Can modify the response before it's returned.
        """
        return response

    async def on_error(
        self, request: Request, error: Exception, context: MiddlewareContext
    ) -> Response | None:
        """Hook called when an error occurs during request processing."""
        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware chain."""
        context = self._get_context(request)

        try:
            # Pre-processing hook
            pre_response = await self.pre_process(request, context)
            if pre_response is not None:
                return pre_response

            # Continue to next middleware/handler
            response = await call_next(request)

            # Post-processing hook
            return await self.post_process(request, response, context)

        except Exception as e:
            # Error handling hook
            error_response = await self.on_error(request, e, context)
            if error_response is not None:
                return error_response
            raise


class MiddlewareManager:
    """Manages the registration and execution of middleware components."""

    def __init__(self, app):
        self.app = app
        self._middleware_registry: dict[str, dict[str, Any]] = {}
        self.logger = logging.getLogger("easymcp.middleware.manager")

    def register_middleware(self, middleware_class: type, **kwargs) -> None:
        """Register a middleware class with optional configuration."""
        name = middleware_class.__name__

        if name in self._middleware_registry:
            self.logger.warning(f"Middleware {name} is already registered")
            return

        # Determine priority for EasyMCPMiddleware instances
        priority_value = (
            middleware_class.priority.value
            if hasattr(middleware_class, "priority") and hasattr(middleware_class.priority, "value")
            else 500  # Default priority for non-EasyMCPMiddleware
        )

        self._middleware_registry[name] = {
            "class": middleware_class,
            "config": kwargs,
            "enabled": True,
            "priority": priority_value,
        }

        self.logger.info(f"Registered middleware: {name} (priority: {priority_value})")

    def unregister_middleware(self, name: str) -> None:
        """Unregister a middleware by name."""
        if name in self._middleware_registry:
            del self._middleware_registry[name]
            self.logger.info(f"Unregistered middleware: {name}")

    def enable_middleware(self, name: str) -> None:
        """Enable a middleware by name."""
        if name in self._middleware_registry:
            self._middleware_registry[name]["enabled"] = True
            self.logger.info(f"Enabled middleware: {name}")

    def disable_middleware(self, name: str) -> None:
        """Disable a middleware by name."""
        if name in self._middleware_registry:
            self._middleware_registry[name]["enabled"] = False
            self.logger.info(f"Disabled middleware: {name}")

    def get_middleware_config(self, name: str) -> dict[str, Any]:
        """Get configuration for a middleware by name."""
        if name in self._middleware_registry:
            return self._middleware_registry[name]["config"]
        return {}

    def setup_middleware_chain(self) -> None:
        """Setup the middleware chain in the correct order."""
        # Get enabled middleware sorted by priority (descending)
        enabled_middleware = [
            (name, info) for name, info in self._middleware_registry.items() if info["enabled"]
        ]

        # Sort by priority (highest priority first)
        enabled_middleware.sort(
            key=lambda x: x[1]["priority"],
            reverse=True,
        )

        self.logger.info("Setting up middleware chain:")
        for name, info in enabled_middleware:
            middleware_class = info["class"]
            config = info["config"]

            # Add to FastAPI app
            self.app.add_middleware(middleware_class, **config)

            priority_name = (
                middleware_class.priority.name
                if hasattr(middleware_class, "priority")
                and hasattr(middleware_class.priority, "name")
                else "DEFAULT"
            )
            self.logger.info(f"  - {name} (priority: {priority_name})")

    def get_middleware_status(self) -> dict[str, dict[str, Any]]:
        """Get the status of all registered middleware."""
        status = {}
        for name, info in self._middleware_registry.items():
            priority_name = (
                info["class"].priority.name
                if hasattr(info["class"], "priority") and hasattr(info["class"].priority, "name")
                else "UNKNOWN"
            )
            status[name] = {
                "enabled": info["enabled"],
                "class": info["class"].__name__,
                "priority": priority_name,
            }
        return status


class SecurityHeadersMiddleware(EasyMCPMiddleware):
    """Middleware to add security headers to all responses."""

    @property
    def name(self) -> str:
        return "SecurityHeadersMiddleware"

    def __init__(self, app):
        super().__init__(app, priority=MiddlewarePriority.SECURITY)

    async def post_process(
        self, request: Request, response: Response, context: MiddlewareContext
    ) -> Response:
        """Add security headers to the response."""
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class MetricsTrackerMiddleware(EasyMCPMiddleware):
    """Middleware to track API request metrics and performance."""

    @property
    def name(self) -> str:
        return "MetricsTrackerMiddleware"

    def __init__(self, app):
        super().__init__(app, priority=MiddlewarePriority.METRICS)

    async def pre_process(self, request: Request, context: MiddlewareContext) -> None:
        """Start tracking request metrics."""
        # Store start time in context
        context.data["metrics_start_time"] = time.time()

        # Update global request count
        app_state = request.app.state.app_state
        app_state.request_total += 1

        return None

    async def post_process(
        self, request: Request, response: Response, context: MiddlewareContext
    ) -> Response:
        """Record metrics after request processing."""
        # Calculate response time
        start_time = context.data.get("metrics_start_time", context.start_time)
        response_time = time.time() - start_time

        # Record performance metrics
        performance_monitor.record_request_time(response_time)

        # Update success/failure counters
        app_state = request.app.state.app_state
        if 200 <= response.status_code < 400:
            app_state.request_successful += 1
        else:
            app_state.request_failed += 1

        return response


class ActivityTrackerMiddleware(EasyMCPMiddleware):
    """Middleware to track API activity."""

    @property
    def name(self) -> str:
        return "ActivityTrackerMiddleware"

    def __init__(self, app):
        super().__init__(app, priority=MiddlewarePriority.BUSINESS_LOGIC)

    async def pre_process(self, request: Request, context: MiddlewareContext) -> None:
        """Track API activity."""
        # Update the last activity timestamp
        request.app.state.app_state.api_last_activity = datetime.now(UTC)

        return None
