"""PriceDrop Tracker — FastAPI backend entrypoint."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import init_db
from .logging_config import configure_logging
from .middleware.logging import RequestLoggingMiddleware
from .middleware.security import SecurityMiddleware
from .routers import products, stats
from .services.checker import checker
from .services.health import health_status
from .version import __version__


configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    if settings.checker_enabled:
        # Apply the configured interval (CHECKER_INTERVAL_SECONDS) to the
        # module-level singleton before starting it.
        checker.interval = max(
            int(settings.checker_interval_seconds), checker.MIN_INTERVAL_SECONDS
        )
        checker.start()
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

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
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


app.include_router(products.router)
app.include_router(stats.router)

# Web dashboard (served at /dashboard)
_dashboard_dir = Path(__file__).resolve().parent.parent.parent / "web"
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(_dashboard_dir), html=True), name="dashboard")
