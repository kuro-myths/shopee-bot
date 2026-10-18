"""Shared fixtures for the test suite.

The database URL is redirected to a temporary file BEFORE the app
modules are imported, so `db.py` picks up the test database.
"""
import os
import tempfile

import pytest

# Redirect the database to a temp file before importing the app
_tmpdir = tempfile.mkdtemp(prefix="pdt-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmpdir, 'test.db')}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """TestClient with a clean database per test."""
    from app.db import db, init_db
    from app.middleware.security import _hits

    init_db()
    # Reset all tables so each test starts from an empty database
    with db() as conn:
        conn.execute("DELETE FROM price_history")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM sqlite_sequence")  # reset AUTOINCREMENT
    _hits.clear()  # reset rate limiter between tests
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sample_product():
    return {
        "url": "https://shopee.co.id/example-i.123.456",
        "name": "Contoh Produk",
        "marketplace": "shopee",
        "image": "",
        "current_price": 100000,
    }
