"""Unit tests for configuration parsing."""
import os

from app.config import Settings


def test_default_threshold():
    s = Settings()
    assert s.drop_threshold_pct == 5.0


def test_threshold_from_env(monkeypatch):
    monkeypatch.setenv("DROP_THRESHOLD_PCT", "10")
    s = Settings()
    assert s.drop_threshold_pct == 10.0


def test_empty_credentials_default():
    s = Settings()
    assert s.telegram_bot_token == ""
    assert s.shopee_app_secret == ""


def test_database_url_default():
    s = Settings()
    assert s.database_url.startswith("sqlite:///")
