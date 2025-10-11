"""Graceful shutdown handler for the EasyMCP application."""

import asyncio
import logging
import signal
from typing import Any

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Handles graceful shutdown of the application."""

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks = set()

    def handle_signal(self, sig: int, frame: Any = None) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"\nReceived {signal.Signals(sig).name}, initiating graceful shutdown...")
        self.shutdown_event.set()

    def track_task(self, task: asyncio.Task) -> None:
        """Track tasks for cleanup during shutdown."""
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()

    async def cancel_all_tasks(self) -> None:
        """Cancel all tracked tasks."""
        for task in list(self.tasks):
            if not task.done():
                logger.debug(f"Cancelling task: {task}")
                task.cancel()

        # Wait for all tasks to complete
        if self.tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.tasks, return_exceptions=True), timeout=5.0
                )
            except TimeoutError:
                logger.warning("Some tasks did not complete within timeout during shutdown")

    def is_shutting_down(self) -> bool:
        """Check if shutdown has been initiated."""
        return self.shutdown_event.is_set()
