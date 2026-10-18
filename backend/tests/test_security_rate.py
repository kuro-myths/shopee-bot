"""Tests for rate limiting behaviour."""
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.security import LIMIT, _hits


def test_rate_limit_triggers_429(client, monkeypatch):
    monkeypatch.setattr("app.middleware.security.LIMIT", 3)
    _hits.clear()
    with TestClient(app) as c:
        for _ in range(3):
            assert c.get("/api/products").status_code == 200
        res = c.get("/api/products")
        assert res.status_code == 429


def test_rate_limit_resets(client, monkeypatch):
    monkeypatch.setattr("app.middleware.security.LIMIT", 2)
    _hits.clear()
    with TestClient(app) as c:
        c.get("/api/products")
        c.get("/api/products")
        assert c.get("/api/products").status_code == 429
    _hits.clear()
    with TestClient(app) as c:
        assert c.get("/api/products").status_code == 200
