"""Unit tests for the health service."""
from app.db import db, init_db
from app.services.health import health_status


def setup_module():
    init_db()


def test_health_reports_ok():
    status = health_status()
    assert status["status"] == "ok"
    assert status["database"] == "ok"
    assert status["uptime_seconds"] >= 0


def test_health_counts_products():
    with db() as conn:
        conn.execute(
            "INSERT INTO products (url, name, marketplace) VALUES (?, ?, ?)",
            ("https://shopee.co.id/h-i.1.1", "H", "shopee"),
        )
    status = health_status()
    assert status["products_tracked"] >= 1
