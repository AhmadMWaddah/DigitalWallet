"""
Tests for structured JSON logging.

Verifies every console log line parses as JSON with the expected fields.
"""

import json
import logging


class TestJsonFormatter:
    """Test core.logging.JsonFormatter output shape."""

    def _record(self, message="hello", level=logging.INFO):
        """Build a LogRecord for formatting."""
        return logging.LogRecord(
            name="wallet",
            level=level,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )

    def test_output_is_json_with_required_fields(self):
        """Test formatted line parses with timestamp/level/logger/message."""
        from core.logging import JsonFormatter

        line = JsonFormatter().format(self._record())

        payload = json.loads(line)
        assert payload["level"] == "INFO"
        assert payload["logger"] == "wallet"
        assert payload["message"] == "hello"
        assert "timestamp" in payload

    def test_format_args_interpolated(self):
        """Test %-style args render into the message string."""
        from core.logging import JsonFormatter

        record = logging.LogRecord(
            name="ops",
            level=logging.WARNING,
            pathname=__file__,
            lineno=2,
            msg="flagged %s",
            args=("TX-1",),
            exc_info=None,
        )

        payload = json.loads(JsonFormatter().format(record))
        assert payload["message"] == "flagged TX-1"
        assert payload["level"] == "WARNING"
