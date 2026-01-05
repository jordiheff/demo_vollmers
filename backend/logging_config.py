"""
Structured logging configuration for the application.
Provides JSON-formatted logs for production and human-readable logs for development.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Optional
from config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON for production environments.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        return json.dumps(log_data)


class DevFormatter(logging.Formatter):
    """
    Human-readable formatter for development environments.
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"{color}{timestamp} | {record.levelname:8} | {record.name} | {record.getMessage()}{self.RESET}"

        # Add extra data if present
        if hasattr(record, "extra_data") and record.extra_data:
            message += f"\n    Data: {record.extra_data}"

        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class StructuredLogger:
    """
    Wrapper around standard logger that adds structured data support.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, data: Optional[dict] = None, **kwargs):
        """Internal logging method that adds extra data."""
        extra = {"extra_data": data} if data else {}
        self.logger.log(level, message, extra=extra, **kwargs)

    def debug(self, message: str, data: Optional[dict] = None, **kwargs):
        """Log debug message with optional structured data."""
        self._log(logging.DEBUG, message, data, **kwargs)

    def info(self, message: str, data: Optional[dict] = None, **kwargs):
        """Log info message with optional structured data."""
        self._log(logging.INFO, message, data, **kwargs)

    def warning(self, message: str, data: Optional[dict] = None, **kwargs):
        """Log warning message with optional structured data."""
        self._log(logging.WARNING, message, data, **kwargs)

    def error(self, message: str, data: Optional[dict] = None, **kwargs):
        """Log error message with optional structured data."""
        self._log(logging.ERROR, message, data, **kwargs)

    def critical(self, message: str, data: Optional[dict] = None, **kwargs):
        """Log critical message with optional structured data."""
        self._log(logging.CRITICAL, message, data, **kwargs)

    def exception(self, message: str, data: Optional[dict] = None, **kwargs):
        """Log exception with traceback and optional structured data."""
        extra = {"extra_data": data} if data else {}
        self.logger.exception(message, extra=extra, **kwargs)


def setup_logging() -> None:
    """
    Configure logging for the application.
    Uses JSON formatter in production, human-readable in development.
    """
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers.clear()

    # Set log level based on debug mode
    log_level = logging.DEBUG if settings.debug else logging.INFO
    root_logger.setLevel(log_level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Use JSON formatter in production, dev formatter in debug mode
    if settings.debug:
        handler.setFormatter(DevFormatter())
    else:
        handler.setFormatter(JSONFormatter())

    root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Pre-configured loggers for common modules
class Loggers:
    """Pre-configured logger instances for application modules."""

    @staticmethod
    def extraction() -> StructuredLogger:
        return get_logger("extraction")

    @staticmethod
    def calculation() -> StructuredLogger:
        return get_logger("calculation")

    @staticmethod
    def label_generation() -> StructuredLogger:
        return get_logger("label_generation")

    @staticmethod
    def api() -> StructuredLogger:
        return get_logger("api")

    @staticmethod
    def usda() -> StructuredLogger:
        return get_logger("usda")
