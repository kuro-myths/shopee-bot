"""Rate limit configuration.

Kept separate from config.py so the middleware can re-read values
without a circular import, and so tests can tweak them independently.
"""
import os

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
