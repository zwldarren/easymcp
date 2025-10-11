"""Main entry point for the EasyMCP application."""

import argparse
import asyncio
import contextlib
import logging
import signal
import sys
from importlib.metadata import version

import uvicorn

from easymcp.api.main import app
from easymcp.config import get_settings, setup_logging
from easymcp.core.graceful_shutdown import GracefulShutdown
from easymcp.state import app_state

# Set up logger for this module
logger = logging.getLogger(__name__)


def _setup_argument_parser() -> argparse.ArgumentParser:
    """Set up and return the argument parser for the MCP proxy."""
    try:
        package_version = version("EasyMCP")
    except Exception:
        package_version = "unknown"

    parser = argparse.ArgumentParser(
        description=("Starts the EasyMCP API server."),
        epilog=("Examples:\n  easymcp --port 8080\n  easymcp --host 0.0.0.0 --port 8080\n"),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version}",
        help="Show the version and exit",
    )

    settings_obj = get_settings()
    parser.add_argument(
        "--host",
        default=settings_obj.host,
        help=f"Host to bind the API server on. Default is {settings_obj.host}",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=settings_obj.port,
        help=f"Port to bind the API server on. Default is {settings_obj.port}",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging output.",
        default=False,
    )

    return parser


async def _startup_with_config(uvicorn_log_level: str) -> None:
    """Start the server and load configuration with graceful shutdown."""
    # Create shutdown handler
    shutdown_handler = GracefulShutdown()

    # Set up server config
    server_config = uvicorn.Config(
        app, host=app_state.host, port=app_state.port, log_level=uvicorn_log_level
    )
    server = uvicorn.Server(server_config)

    # Setup signal handlers
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            # Create a closure that captures the current signal value by passing it as parameter
            def make_signal_handler(signal_value):
                return lambda: shutdown_handler.handle_signal(signal_value)

            loop.add_signal_handler(sig, make_signal_handler(sig))  # type: ignore
    except NotImplementedError:
        logger.warning(
            "loop.add_signal_handler is not available on this platform. Using signal.signal()."
        )
        for sig in (signal.SIGINT, signal.SIGTERM):
            # Create a closure that captures the current signal value by passing it as parameter
            def make_signal_handler(signal_value):
                return lambda s, f: shutdown_handler.handle_signal(signal_value)

            signal.signal(sig, make_signal_handler(sig))

    # Start the server in a task
    server_task = asyncio.create_task(server.serve())
    shutdown_handler.track_task(server_task)

    try:
        # Wait for either server to fail or a shutdown signal
        shutdown_wait_task = asyncio.create_task(shutdown_handler.wait_for_shutdown())
        done, pending = await asyncio.wait(
            [server_task, shutdown_wait_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if server_task in done:
            # Check if server task raised an exception
            try:
                server_task.result()
                logger.warning("Server task exited unexpectedly. Initiating shutdown.")
            except SystemExit:
                logger.exception("Server failed to start")
                raise
            except Exception:
                logger.exception("Server task failed with exception")
                raise
            shutdown_handler.shutdown_event.set()

        # Cancel pending tasks
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        # Initiate graceful shutdown
        logger.info("Initiating server shutdown...")
        server.should_exit = True

        # Cancel all tracked tasks
        await shutdown_handler.cancel_all_tasks()

    except SystemExit:
        # Re-raise SystemExit to allow proper program termination
        logger.info("Server startup failed, exiting...")
        raise
    except Exception:
        logger.exception("Error during server execution")
        raise
    finally:
        # Ensure all servers are stopped
        if app_state.server_manager:
            try:
                await asyncio.wait_for(app_state.server_manager.stop_all_servers(), timeout=5.0)
            except TimeoutError:
                logger.warning("Server shutdown timed out, forcing exit")
        logger.info("Application shutdown complete")


def main() -> None:
    """Parse command-line arguments and start the MCP Proxy API server."""
    parser = _setup_argument_parser()
    args = parser.parse_args()

    # Set up logging with validation
    try:
        log_level = "DEBUG" if args.debug else "INFO"
        setup_logging(log_level=log_level)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    uvicorn_log_level = "debug" if args.debug else "info"

    app_state.host = args.host
    app_state.port = args.port

    logger.info(f"Starting EasyMCP API server on {args.host}:{args.port}")

    # Start the server and load config with proper signal handling
    try:
        asyncio.run(_startup_with_config(uvicorn_log_level))
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception:
        logger.exception("Unexpected error")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
