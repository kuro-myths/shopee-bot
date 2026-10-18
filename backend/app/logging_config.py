"""Structured logging configuration for the price tracker backend.

Logs are emitted as JSON lines when ``LOG_FORMAT=json`` so they can be
consumed by log aggregators (Loki, ELK, CloudWatch). Plain text is used by
default for local development.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class JsonFormatter(logging.Formatter):
    """Minimal JSON lines formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def get_log_level() -> int:
    """Resolve the log level from the environment."""
    return _LEVELS.get(os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)


def configure_logging() -> None:
    """Configure the root logger once per process."""
    root = logging.getLogger()
    # Never reconfigure when our own handlers are already installed; also
    # keep uvicorn's pre-configured root handlers intact but still expose
    # a JSON formatter on our namespace logger when LOG_FORMAT=json.
    if any(
        getattr(h, "pricedrop_configured", False) for h in root.handlers
    ):
        return

    fmt = os.getenv("LOG_FORMAT", "text")
    if fmt == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
            )
        )
    handler.setLevel(get_log_level())
    handler.pricedrop_configured = True
    root.addHandler(handler)
    root.setLevel(get_log_level())
    # Keep uvicorn's access log readable but lower noisy third-party logs.
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # When uvicorn pre-configured handlers, apply the JSON formatter to
    # our namespace logger so LOG_FORMAT=json still works in production.
    if fmt == "json":
        pricedrop_logger = logging.getLogger("pricedrop")
        if not pricedrop_logger.handlers:
            pricedrop_logger.handlers = [handler]
            pricedrop_logger.propagate = False
