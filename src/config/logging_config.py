"""
Structured logging configuration using structlog.

Provides JSON and console logging with contextual information.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.config.settings import get_settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log events.

    Args:
        logger: Logger instance
        method_name: Method name being called
        event_dict: Event dictionary

    Returns:
        EventDict: Enhanced event dictionary
    """
    settings = get_settings()
    event_dict["app_name"] = settings.app_name
    event_dict["app_version"] = settings.app_version
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging based on settings.

    Sets up processors, formatters, and output handlers.
    """
    settings = get_settings()

    # Ensure log directory exists
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Choose processors based on format
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.debug_mode:
        processors.append(structlog.processors.ExceptionPrettyPrinter())
    else:
        processors.append(structlog.processors.format_exc_info)

    # Add appropriate renderer
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup file handler if log file is configured
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(getattr(logging, settings.log_level))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (defaults to caller's module)

    Returns:
        BoundLogger: Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_started", query="revenue analysis", user_id=123)
    """
    return structlog.get_logger(name)


# Context manager for adding temporary context
class log_context:
    """
    Context manager for adding temporary logging context.

    Example:
        >>> with log_context(user_id=123, session_id="abc"):
        ...     logger.info("processing_query")
        # Output includes user_id and session_id
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize context manager.

        Args:
            **kwargs: Context key-value pairs to add
        """
        self.context = kwargs

    def __enter__(self) -> None:
        """Enter context and bind variables."""
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**self.context)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and clear variables."""
        structlog.contextvars.clear_contextvars()
