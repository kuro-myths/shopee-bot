"""Request logging middleware."""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger("pricedrop.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        log.info(
            "%s %s -> %s (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            round(duration_ms, 1),
        )
        return response
