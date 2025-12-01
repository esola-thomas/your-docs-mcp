"""Structured logging setup for the MCP server."""

import logging
import sys
from typing import Any

# Create logger instance
logger = logging.getLogger("docs_mcp")


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Configure logger
    logger.setLevel(log_level)
    logger.addHandler(handler)
    logger.propagate = False


def audit_log(event: str, details: dict[str, Any]) -> None:
    """Log security audit events.

    Args:
        event: Event type (e.g., "file_access", "path_violation", "search_query")
        details: Event details dictionary
    """
    logger.info(f"AUDIT: {event}", extra={"audit": True, "event": event, "details": details})
