"""Security middleware: API key auth and simple rate limiting.

When API_KEY is configured, requests must carry `X-API-Key` (or the
`token` query parameter). Rate limiting is a lightweight in-memory
sliding window per client IP / API key.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import settings
from ..services.limits import RATE_LIMIT_REQUESTS as LIMIT, RATE_LIMIT_WINDOW_SECONDS as WINDOW

# Per-key: deque of request timestamps
_hits = defaultdict(deque)


def _client_key(request: Request) -> str:
    key = request.headers.get("X-API-Key")
    if key:
        return f"key:{key}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


def _hit_window(key: str) -> tuple[bool, int, int]:
    """Record a hit; return (limited, remaining, reset_in_seconds)."""
    now = time.time()
    window = _hits[key]
    while window and now - window[0] > WINDOW:
        window.popleft()
    if len(window) >= LIMIT:
        remaining = 0
        reset_in = max(1, int(WINDOW - (now - window[0])) + 1) if window else WINDOW
        return True, remaining, reset_in
    window.append(now)
    return False, LIMIT - len(window), int(WINDOW - (now - window[0])) if window else WINDOW


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth/rate-limit for docs and health
        path = request.url.path
        # Metadata endpoints are public; everything else needs auth
        if path in ("/docs", "/openapi.json", "/health", "/api/version") or path.startswith("/redoc"):
            return await call_next(request)

        if settings.api_key:
            provided = request.headers.get("X-API-Key") or request.query_params.get("token")
            if provided != settings.api_key:
                return JSONResponse({"detail": "Invalid API key"}, status_code=401)

        key = _client_key(request)
        limited, remaining, reset_in = _hit_window(key)
        headers = {
            "X-RateLimit-Limit": str(LIMIT),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_in),
        }
        if limited:
            return JSONResponse(
                {"detail": f"Rate limit exceeded: {LIMIT} requests per {WINDOW}s"},
                status_code=429,
                headers=headers,
            )

        response = await call_next(request)
        for name, value in headers.items():
            response.headers[name] = value
        return response
