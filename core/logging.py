"""
Structured logging helpers.

Stdlib-only JSON formatter so every stdout log line is machine-readable
(Loki, CloudWatch, or any log agent) without extra dependencies.
"""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record):
        """Render record with timestamp, level, logger, and message."""
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)
