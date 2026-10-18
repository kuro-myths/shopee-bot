"""Health check helpers."""
import time

from ..db import db
from ..version import __version__

STARTED_AT = time.time()


def _schema_version():
    try:
        with db() as conn:
            row = conn.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            ).fetchone()
            return row["version"] if row else None
    except Exception:
        return None


def health_status():
    """Return a health payload with database connectivity."""
    db_ok = True
    product_count = 0
    try:
        with db() as conn:
            conn.execute("SELECT 1").fetchone()
            product_count = conn.execute(
                "SELECT COUNT(*) AS c FROM products WHERE archived = 0"
            ).fetchone()["c"]
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "uptime_seconds": round(time.time() - STARTED_AT),
        "database": "ok" if db_ok else "error",
        "products_tracked": product_count,
        "version": __version__,
        "schema_version": _schema_version(),
    }
