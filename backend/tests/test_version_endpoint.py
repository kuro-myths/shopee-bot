"""Tests for the /api/version endpoint."""
from app.version import __version__


def test_version_endpoint(client):
    res = client.get("/api/version")
    assert res.status_code == 200
    body = res.json()
    assert body["version"] == __version__
    assert body["api_version"] == 1


def test_health_reports_version(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["version"] == __version__
    assert "schema_version" in res.json()
