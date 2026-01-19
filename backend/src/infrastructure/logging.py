"""Structured logging configuration with PII redaction."""
import logging
import sys
import re
from typing import Any, Dict
import structlog


# Patterns for PII detection
PII_PATTERNS = [
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]'),  # Credit card
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
    (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]'),  # Phone
    (r'\b\d{10}\b', '[PHONE]'),  # 10-digit phone
]


def redact_pii(message: str) -> str:
    """Redact PII from log messages."""
    redacted = message
    for pattern, replacement in PII_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


class PIIRedactingProcessor:
    """Processor to redact PII from log records."""
    
    def __call__(self, logger, method_name, event_dict):
        """Process log event to redact PII."""
        if 'event' in event_dict:
            event_dict['event'] = redact_pii(str(event_dict['event']))
        if 'message' in event_dict:
            event_dict['message'] = redact_pii(str(event_dict['message']))
        return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with PII redaction."""
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            PIIRedactingProcessor(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)
