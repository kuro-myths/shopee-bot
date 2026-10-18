"""Telegram notifier with retry and backoff.

Sends drop/target alerts to a configured chat. The primary notifier used
to fire a single request and swallow failures; this version adds bounded
retries with exponential backoff so transient network errors (5xx,
timeouts) do not silently drop alerts.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

from ..config import settings

logger = logging.getLogger(__name__)

DEFAULT_RETRIES = int(os.getenv("NOTIFY_RETRIES", "3"))
DEFAULT_BACKOFF = float(os.getenv("NOTIFY_BACKOFF", "0.5"))
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class NotifyError(Exception):
    """Raised when all notification attempts fail."""


def _build_payload(text: str) -> bytes:
    return json.dumps(
        {
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
    ).encode()


def send_telegram(
    text: str, retries: int = DEFAULT_RETRIES, backoff: float = DEFAULT_BACKOFF
) -> bool:
    """Send ``text`` to the configured Telegram chat.

    Returns ``False`` when the bot is not configured, ``True`` when
    Telegram accepted the message, and raises :class:`NotifyError` when
    every attempt failed.
    """
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("telegram not configured, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    data = _build_payload(text)
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )

    attempt = 0
    while True:
        attempt += 1
        try:
            with urllib.request.urlopen(request, timeout=10) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status in RETRYABLE_STATUS and attempt < retries:
                delay = backoff * (2 ** (attempt - 1))
                logger.warning("telegram returned %s, retry in %.1fs", status, delay)
                time.sleep(delay)
                continue
            raise NotifyError(f"telegram returned {status}") from exc
        except OSError as exc:  # network-level failure (timeout, reset, ...)
            if attempt < retries:
                delay = backoff * (2 ** (attempt - 1))
                logger.warning("telegram request error (%s), retry in %.1fs", exc, delay)
                time.sleep(delay)
                continue
            raise NotifyError(
                f"telegram send failed after {attempt} attempts"
            ) from exc
