"""
Structured logging configuration for the AI Code Review Agent.

This module sets up structured logging using structlog with
JSON formatting for production environments.
"""
import logging
import sys
from typing import Any, Dict

# Optional import for structlog
try:
    import structlog
    from structlog.types import Processor
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    structlog = None
    Processor = None

from app.core.config import get_settings


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add correlation ID to log entries for request tracing.
    
    Args:
        logger: Logger instance
        method_name: Method name being logged
        event_dict: Log event dictionary
        
    Returns:
        Dict[str, Any]: Updated event dictionary with correlation ID
    """
    # Try to get correlation ID from context
    # This would be set by middleware in a real application
    correlation_id = getattr(logger, '_correlation_id', None)
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    
    return event_dict


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up structlog with appropriate processors for development
    and production environments.
    """
    if not STRUCTLOG_AVAILABLE:
        # Fall back to standard logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
        )
        return
        
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    )
    
    # Structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_correlation_id,
    ]
    
    if settings.DEBUG:
        # Pretty printing for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON formatting for production
        processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance (structlog.BoundLogger or standard Logger)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin class to add logging capability to other classes.
    
    Provides a 'logger' property that returns a structured logger
    with the class name as the logger name.
    """
    
    @property
    def logger(self):
        """Get logger instance for this class."""
        return get_logger(self.__class__.__name__)
