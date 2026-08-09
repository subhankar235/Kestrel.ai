"""Structured JSON logging that feeds both the self-audit and observability layers.

Phase 21 additions:
  - capture_exception(): sends exceptions to Sentry (no-ops when SENTRY_DSN is not set).
  - log_activity_failure(): structured ERROR log for Temporal activity failures with error
    classification (retryable vs non-retryable), source, and cycle context.

Phase 22 additions:
  - init_sentry(): initializes Sentry SDK with ENVIRONMENT tagging for FastAPI process and Temporal worker.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


_RESERVED_LOG_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON with an ISO-8601 UTC timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Include custom extra attributes passed via extra={...}
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_ATTRS and key not in payload:
                payload[key] = value

        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)

        return json.dumps(payload, default=str)



def setup_logging(level: int = logging.INFO, name: str = "kestrel") -> logging.Logger:
    """Install a JSON stdout handler on the given logger and return it."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = True
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger with the JSON handler attached."""
    setup_logging()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger



def init_sentry(process_name: str = "fastapi") -> None:
    """Initialize Sentry SDK if SENTRY_DSN is configured, tagging events by environment and process."""
    from app.core.config import get_settings  # noqa: PLC0415

    settings = get_settings()
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk  # noqa: PLC0415

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1,
                server_name=f"kestrel-{process_name}",
            )
            get_logger(__name__).info(
                f"Sentry initialized for process '{process_name}'",
                extra={
                    "event": "sentry_init",
                    "environment": settings.ENVIRONMENT,
                    "process_name": process_name,
                },
            )
        except Exception as exc:  # noqa: BLE001
            get_logger(__name__).warning(
                f"Failed to initialize Sentry SDK: {exc}",
                extra={"error": str(exc)},
            )


def capture_exception(exc: BaseException, context: dict[str, Any] | None = None) -> None:
    """Report an exception to Sentry when configured; silently no-ops otherwise.

    This is the single authoritative call site for Sentry so the rest of the codebase
    never imports sentry_sdk directly.
    """
    try:
        import sentry_sdk  # noqa: PLC0415

        if context:
            for key, value in context.items():
                sentry_sdk.set_extra(key, value)
        sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001
        # Sentry SDK not installed or not initialized — silently ignore.
        pass


def log_activity_failure(
    logger: logging.Logger,
    *,
    activity: str,
    error: BaseException,
    agent_id: str | None = None,
    cycle_count: int | None = None,
    retryable: bool = True,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a structured ERROR log for a Temporal Activity failure and capture it in Sentry.

    Args:
        logger: The named logger for the calling module.
        activity: Human-readable name of the failing activity (e.g., "discover_topics_activity").
        error: The caught exception.
        agent_id: Agent ID for correlation in log aggregation.
        cycle_count: Current cycle number, if known.
        retryable: Whether Temporal will retry this failure.
        extra: Additional key-value pairs to include in the log payload.
    """
    context: dict[str, Any] = {
        "event": "activity_failure",
        "activity": activity,
        "error_type": type(error).__name__,
        "error": str(error),
        "retryable": retryable,
    }
    if agent_id is not None:
        context["agent_id"] = agent_id
    if cycle_count is not None:
        context["cycle_count"] = cycle_count
    if extra:
        context.update(extra)

    logger.error(
        f"Activity '{activity}' failed [retryable={retryable}]: {error}",
        extra=context,
    )
    capture_exception(error, context=context)