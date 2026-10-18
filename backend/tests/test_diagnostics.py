"""Tests for diagnostics, error capture, and Railway-related hardening."""
import os

import pytest
from fastapi.testclient import TestClient

from app import db as dbmod
from app.config import settings
from app.main import app
from app.services import diagnostics, errorlog


def _by_id(report):
    return {c["id"]: c for c in report["checks"]}


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    errorlog.clear()
    for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_NAME", "RAILWAY_VOLUME_MOUNT_PATH"):
        monkeypatch.delenv(k, raising=False)
    yield
    errorlog.clear()


def test_diagnostics_endpoint_shape(client):
    r = client.get("/api/diagnostics")
    assert r.status_code == 200
    body = r.json()
    assert body["overall"] in ("ok", "warn", "error")
    assert {"checks", "recent_errors", "platform"} <= set(body)
    assert _by_id(body)["database"]["status"] == "ok"


def test_diagnostics_requires_api_key_when_set(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "rahasia")
    assert client.get("/api/diagnostics").status_code == 401
    assert client.get("/api/diagnostics", headers={"X-API-Key": "rahasia"}).status_code == 200


def test_secrets_never_leak(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "SUPERSECRETKEY")
    monkeypatch.setattr(settings, "telegram_bot_token", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789")
    text = str(diagnostics.run_checks())
    assert "SUPERSECRETKEY" not in text
    assert "ABCdefGHI" not in text


def test_telegram_checks(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    assert _by_id(diagnostics.run_checks())["telegram"]["status"] == "info"
    monkeypatch.setattr(settings, "telegram_bot_token", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789")
    assert _by_id(diagnostics.run_checks())["telegram"]["status"] == "warn"  # chat id missing
    monkeypatch.setattr(settings, "telegram_chat_id", "42")
    assert _by_id(diagnostics.run_checks())["telegram"]["status"] == "ok"
    monkeypatch.setattr(settings, "telegram_bot_token", "bukan-token")
    assert _by_id(diagnostics.run_checks())["telegram"]["status"] == "warn"  # bad format


def test_partial_affiliate_credentials_warn(monkeypatch):
    monkeypatch.setattr(settings, "shopee_app_id", "x")
    monkeypatch.setattr(settings, "shopee_app_secret", "")
    monkeypatch.setattr(settings, "shopee_partner_id", "")
    assert _by_id(diagnostics.run_checks())["affiliate"]["status"] == "warn"


def test_railway_without_volume_warns(monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    checks = _by_id(diagnostics.run_checks())
    assert checks["persistence"]["status"] == "warn"
    assert "Volume" in checks["persistence"]["fix"]
    assert checks["api_key"]["status"] in ("warn", "ok")


def test_railway_with_volume_ok(monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", os.path.dirname(dbmod.DB_PATH))
    assert _by_id(diagnostics.run_checks())["persistence"]["status"] == "ok"


def test_db_fallback_is_reported(monkeypatch):
    monkeypatch.setattr(dbmod, "DB_FALLBACK_REASON", "/data tidak bisa ditulis")
    c = _by_id(diagnostics.run_checks())["database"]
    assert c["status"] == "error" and "Volume" in c["fix"]


def test_resolve_db_path_falls_back_when_unwritable(tmp_path, monkeypatch):
    # A path under a regular file can never be created as a directory
    blocker = tmp_path / "file"
    blocker.write_text("x")
    monkeypatch.chdir(tmp_path)
    path, reason = dbmod._resolve_db_path(f"sqlite:///{blocker}/sub/x.db")
    assert reason and path == str(tmp_path / "pricedrop.db")


def test_resolve_db_path_creates_missing_directory(tmp_path):
    target = tmp_path / "a" / "b" / "x.db"
    path, reason = dbmod._resolve_db_path(f"sqlite:///{target}")
    assert reason is None and (tmp_path / "a" / "b").is_dir()


def test_unhandled_exception_is_recorded(monkeypatch):
    def boom():
        raise RuntimeError("kaboom")

    app.add_api_route("/api/_boom", boom, methods=["GET"])
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.get("/api/_boom")
            assert r.status_code == 500
            assert r.json() == {"detail": "Internal server error"}
            report = c.get("/api/diagnostics").json()
        assert any("kaboom" in e["message"] for e in report["recent_errors"])
        assert _by_id(report)["errors"]["status"] == "warn"
    finally:
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", "") != "/api/_boom"]


def test_dashboard_static_is_public_with_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "rahasia")
    r = client.get("/dashboard/", follow_redirects=True)
    assert r.status_code == 200 and "PriceDrop" in r.text
    assert client.get("/api/products").status_code == 401


def test_startup_with_checker_enabled(monkeypatch):
    """Regresi: Railway menjalankan CHECKER_ENABLED=true; startup tidak boleh crash.

    (Tes lain memakai CHECKER_ENABLED=false sehingga bug
    `checker.MIN_INTERVAL_SECONDS` tidak pernah tersentuh.)
    """
    from app.services.checker import PriceChecker, checker

    monkeypatch.setattr(settings, "checker_enabled", True)
    monkeypatch.setattr(settings, "checker_interval_seconds", 5)  # di bawah minimum
    monkeypatch.setattr(checker, "check_all", lambda: 0)  # jangan fetch jaringan
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "ok"
        assert checker.interval == PriceChecker.MIN_INTERVAL_SECONDS  # dibatasi ke minimum
    assert checker._thread is None or not checker._thread.is_alive()


def test_checker_failure_does_not_crash_server(monkeypatch):
    from app.services.checker import checker

    def broken():
        raise RuntimeError("checker rusak")

    monkeypatch.setattr(settings, "checker_enabled", True)
    monkeypatch.setattr(checker, "start", broken)
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "ok"  # server tetap hidup
        report = c.get("/api/diagnostics").json()
    assert any("checker rusak" in e["message"] for e in report["recent_errors"])


def test_root_redirects_browser_to_dashboard(client, monkeypatch):
    r = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"}, follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/dashboard/"
    # klien API tetap mendapat JSON
    j = client.get("/", headers={"Accept": "application/json"})
    assert j.status_code == 200 and j.json()["app"] == "PriceDrop Tracker API"
    # tetap bisa dibuka (tanpa 401) walau API_KEY diaktifkan
    monkeypatch.setattr(settings, "api_key", "rahasia")
    r2 = client.get("/", headers={"Accept": "text/html"}, follow_redirects=False)
    assert r2.status_code == 307
    page = client.get("/", headers={"Accept": "text/html"}, follow_redirects=True)
    assert page.status_code == 200 and "PriceDrop" in page.text


def test_dashboard_check_ok_in_repo_layout():
    assert _by_id(diagnostics.run_checks())["dashboard"]["status"] == "ok"


def test_dashboard_missing_is_an_error(monkeypatch):
    from app import main as m

    monkeypatch.setattr(m, "_dashboard_dir", None)
    c = _by_id(diagnostics.run_checks())["dashboard"]
    assert c["status"] == "error" and "COPY web/" in c["fix"]


def test_find_dashboard_dir_env_override_and_docker_layout(tmp_path, monkeypatch):
    from app import main as m

    (tmp_path / "index.html").write_text("<html></html>")
    monkeypatch.setenv("DASHBOARD_DIR", str(tmp_path))
    assert m.find_dashboard_dir() == tmp_path
    monkeypatch.setenv("DASHBOARD_DIR", str(tmp_path / "tidak-ada"))
    assert m.find_dashboard_dir() is not None  # jatuh ke layout repo
