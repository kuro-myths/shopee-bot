"""Tests for the security middleware."""
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.security import LIMIT


def _client_with_api_key(monkeypatch):
    monkeypatch.setattr("app.config.settings.api_key", "test-secret")
    return TestClient(app)


def test_api_key_required_when_configured(client, monkeypatch, sample_product):
    monkeypatch.setattr("app.config.settings.api_key", "test-secret")
    res = client.post("/api/products", json=sample_product)
    assert res.status_code == 401
    res = client.post(
        "/api/products", json=sample_product, headers={"X-API-Key": "test-secret"}
    )
    assert res.status_code == 200


def test_no_api_key_required_when_unset(client, sample_product):
    res = client.post("/api/products", json=sample_product)
    assert res.status_code == 200


def test_health_is_exempt_from_auth(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.api_key", "test-secret")
    res = client.get("/health")
    assert res.status_code == 200
