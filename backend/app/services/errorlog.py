"""In-memory ring buffer of recent server errors (for /api/diagnostics)."""
import time
from collections import deque

_events: deque = deque(maxlen=50)


def record(kind: str, message: str) -> None:
    _events.append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "message": message[:300]})


def recent(limit: int = 20) -> list:
    return list(_events)[-limit:][::-1]


def count() -> int:
    return len(_events)


def clear() -> None:
    _events.clear()
