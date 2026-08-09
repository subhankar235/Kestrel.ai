"""Standalone scheduler worker process entrypoint.

Runs the APScheduler in a standalone process outside of FastAPI.
Useful for running the agent cycle scheduler independently.

Phase 22: Sentry is initialized in the worker process independently of FastAPI so unhandled
exceptions from activities are captured in Sentry tagged with the correct environment.
"""

from __future__ import annotations

import asyncio
import signal

from app.core.config import get_settings
from app.core.logging import get_logger, init_sentry
from app.workflows.schedules import get_scheduler, shutdown_scheduler, start_scheduler

logger = get_logger(__name__)


def _init_sentry() -> None:
    """Initialize Sentry for the worker process (separate from FastAPI)."""
    init_sentry("scheduler-worker")


async def run_worker() -> None:
    """Start the APScheduler and run until interrupted."""
    settings = get_settings()

    # Initialize Sentry for the worker process
    _init_sentry()

    logger.info(
        "Starting standalone scheduler worker",
        extra={
            "task_queue": settings.TEMPORAL_TASK_QUEUE if hasattr(settings, 'TEMPORAL_TASK_QUEUE') else 'kestrel-agent',
            "cycle_interval_minutes": settings.PUBLISH_CYCLE_INTERVAL_MINUTES,
        },
    )

    start_scheduler()

    # Set up graceful shutdown
    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        logger.info("Received shutdown signal, stopping scheduler...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler for all signals
            pass

    logger.info(
        "Scheduler worker listening for jobs...",
        extra={"cycle_interval_minutes": settings.PUBLISH_CYCLE_INTERVAL_MINUTES},
    )

    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_scheduler()
        logger.info("Scheduler worker stopped")


if __name__ == "__main__":
    asyncio.run(run_worker())
