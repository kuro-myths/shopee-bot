"""PriceDrop Tracker — FastAPI backend entrypoint."""
from contextlib import asynccontextmanager
from pathlib import Path

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import init_db
from .logging_config import configure_logging
from .middleware.logging import RequestLoggingMiddleware
from .middleware.security import SecurityMiddleware
from .routers import products, promos, stats
from .services import errorlog
from .services.checker import checker
from .services.diagnostics import run_checks
from .services.health import health_status
from .version import __version__


configure_logging()
logger = logging.getLogger("pricedrop")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # Log a one-line summary of anything misconfigured so it is visible
    # in the Railway deploy logs without opening the dashboard.
    report = run_checks()
    for c in report["checks"]:
        if c["status"] in ("warn", "error"):
            logger.warning("DIAGNOSTIK [%s] %s: %s | Perbaikan: %s", c["status"], c["title"], c["detail"], c["fix"])
    logger.info("Diagnostik startup: %s (platform: %s)", report["overall"], report["platform"])
    if settings.checker_enabled:
        # Kegagalan pengecek harga tidak boleh menjatuhkan seluruh server
        # (Railway akan crash-loop). Catat error-nya; API tetap melayani.
        try:
            # Apply the configured interval (CHECKER_INTERVAL_SECONDS) to the
            # module-level singleton before starting it.
            checker.interval = max(
                int(settings.checker_interval_seconds), checker.MIN_INTERVAL_SECONDS
            )
            checker.start()
        except Exception as exc:
            logger.exception("Pengecek harga gagal start; API tetap berjalan")
            errorlog.record("checker_start", f"{type(exc).__name__}: {exc}")
    yield
    checker.stop()


app = FastAPI(
    title="PriceDrop Tracker API",
    version=__version__,
    description="Track product prices on Shopee & TikTok Shop, detect drops, "
                "and generate affiliate links.",
    lifespan=lifespan,
    contact={"name": "PriceDrop Tracker", "url": "https://github.com/daffaroffi/price-drop-tracker"},
)

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    """Log + remember unexpected errors so /api/diagnostics can show them."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    errorlog.record("unhandled_exception", f"{request.method} {request.url.path}: {type(exc).__name__}: {exc}")
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root(request: Request):
    # Browser (Accept: text/html) -> dashboard; klien API tetap mendapat JSON.
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/dashboard/", status_code=307)
    return {
        "app": "PriceDrop Tracker API",
        "version": __version__,
        "api_version": 1,
        "docs": "/docs",
        "endpoints": [
            "POST /api/products",
            "GET  /api/products",
            "GET  /api/products/{id}",
            "GET  /api/products/{id}/history",
            "GET  /api/products/{id}/summary",
            "PUT  /api/products/{id}/target",
            "PUT  /api/products/{id}/note",
            "POST /api/products/{id}/affiliate",
            "POST /api/products/{id}/archive",
            "POST /api/products/{id}/restore",
            "POST /api/products/prune",
            "DELETE /api/products/{id}",
            "GET  /api/stats",
        ],
    }


@app.get("/health")
def health():
    return health_status()


@app.get("/api/version")
def version():
    """Return the current API version and schema version."""
    return {
        "version": __version__,
        "api_version": 1,
        "schema_version": health_status().get("schema_version"),
    }


@app.get("/api/diagnostics")
def diagnostics():
    """Configuration self-check with suggested fixes (requires API key if set)."""
    return run_checks()


app.include_router(products.router)
app.include_router(stats.router)
app.include_router(promos.router)

# Web dashboard (served at /dashboard)
def find_dashboard_dir():
    """Cari folder dashboard: DASHBOARD_DIR, lalu layout repo (../../web), lalu layout Docker (/app/web)."""
    here = Path(__file__).resolve()
    candidates = [
        Path(os.environ["DASHBOARD_DIR"]) if os.environ.get("DASHBOARD_DIR") else None,
        here.parent.parent.parent / "web",  # repo: backend/app/main.py -> <repo>/web
        here.parent.parent / "web",         # docker: /app/app/main.py -> /app/web
    ]
    for c in candidates:
        if c and (c / "index.html").is_file():
            return c
    return None


_dashboard_dir = find_dashboard_dir()
if _dashboard_dir:
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")
else:
    logger.warning("Folder dashboard (web/index.html) tidak ditemukan; /dashboard akan 404")
