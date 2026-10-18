"""Unit tests for the logging configuration module."""
import json
import logging

from app.logging_config import JsonFormatter, get_log_level


class _Record(logging.LogRecord):
    """LogRecord subclass so we can build records without raising."""

    def __init__(self, name="test", level=logging.INFO, message="hello"):
        self.name = name
        self.levelno = level
        self.levelname = logging.getLevelName(level)
        self.msg = message
        self.args = None
        self.exc_info = None
        self.exc_text = None
        self.stack_info = None
        self.filename = "test_logging_unit.py"
        self.module = "test_logging_unit"
        self.lineno = 1
        self.funcName = "test_record"
        self.created = 1720000000.0
        self.msecs = 0
        self.relativeCreated = 0
        self.thread = 1
        self.threadName = "MainThread"
        self.process = 1
        self.processName = "MainProcess"
        self.taskName = None
        self.extra_fields = None


def test_json_formatter_outputs_valid_json():
    formatter = JsonFormatter()
    line = formatter.format(_Record())
    payload = json.loads(line)
    assert payload["level"] == "INFO"
    assert payload["message"] == "hello"
    assert payload["logger"] == "test"


def test_json_formatter_includes_extra_fields():
    formatter = JsonFormatter()
    record = _Record(message="drop alert")
    record.extra_fields = {"product_id": 7, "drop_pct": 12.5}
    payload = json.loads(formatter.format(record))
    assert payload["product_id"] == 7
    assert payload["drop_pct"] == 12.5


def test_json_formatter_serializes_exceptions():
    formatter = JsonFormatter()
    record = _Record(message="boom")
    try:
        raise ValueError("kaput")
    except ValueError:
        record.exc_info = __import__("sys").exc_info()
    payload = json.loads(formatter.format(record))
    assert "ValueError" in payload["exception"]


def test_get_log_level_defaults_to_info():
    assert get_log_level() == logging.INFO
