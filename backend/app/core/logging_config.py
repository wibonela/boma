"""
Logging configuration for BOMA application.
Provides structured logging with JSON format support.
"""
import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add application context
        log_record["app_name"] = settings.APP_NAME
        log_record["environment"] = settings.ENVIRONMENT
        log_record["level"] = record.levelname

        # Add source information
        if not log_record.get("logger"):
            log_record["logger"] = record.name


def setup_logging() -> None:
    """Configure logging for the application."""

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Choose formatter based on configuration
    if settings.LOG_FORMAT == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Configure uvicorn loggers
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(log_level)
        logger.propagate = False

    # Reduce noise from third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
