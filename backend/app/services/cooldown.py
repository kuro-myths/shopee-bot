"""Notification cooldown.

Prevents alert spam: after a drop notification is sent for a product,
the same product cannot trigger another notification until the cooldown
window has passed (default 24 hours).
"""
import os
import threading
import time

COOLDOWN_SECONDS = int(os.getenv("NOTIFY_COOLDOWN_SECONDS", str(24 * 60 * 60)))

_last_sent = {}
_lock = threading.Lock()


def is_on_cooldown(product_id: int) -> bool:
    """Return True when a notification was recently sent for this product."""
    with _lock:
        last = _last_sent.get(product_id)
        return last is not None and (time.time() - last) < COOLDOWN_SECONDS


def mark_sent(product_id: int):
    with _lock:
        _last_sent[product_id] = time.time()


def should_notify(product_id: int) -> bool:
    """Combined check: skip if on cooldown, otherwise mark and allow."""
    if is_on_cooldown(product_id):
        return False
    mark_sent(product_id)
    return True


def reset():
    """Clear cooldown state (used by tests)."""
    with _lock:
        _last_sent.clear()
