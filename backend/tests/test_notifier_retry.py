"""Unit tests for the notifier retry/backoff logic (no network)."""
import urllib.error

import pytest

from app.services.notifier import NotifyError, send_telegram

# Keep urlopen monkeypatchable without actually hitting the network.


class _FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_not_configured_returns_false(monkeypatch):
    monkeypatch.setattr("app.services.notifier.settings.telegram_bot_token", "")
    monkeypatch.setattr("app.services.notifier.settings.telegram_chat_id", "")
    assert send_telegram("hi") is False


def test_success_on_first_try(monkeypatch):
    monkeypatch.setattr("app.services.notifier.settings.telegram_bot_token", "tok")
    monkeypatch.setattr("app.services.notifier.settings.telegram_chat_id", "123")
    calls = []

    def fake_urlopen(_request, timeout=10):
        calls.append(1)
        return _FakeResponse()

    monkeypatch.setattr("app.services.notifier.urllib.request.urlopen", fake_urlopen)
    assert send_telegram("hi") is True
    assert len(calls) == 1


def test_retries_retryable_status_then_succeeds(monkeypatch):
    monkeypatch.setattr("app.services.notifier.settings.telegram_bot_token", "tok")
    monkeypatch.setattr("app.services.notifier.settings.telegram_chat_id", "123")
    monkeypatch.setattr("app.services.notifier.time.sleep", lambda _s: None)
    calls = []

    def fake_urlopen(_request, timeout=10):
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.HTTPError("u", 503, "unavailable", {}, None)
        return _FakeResponse()

    monkeypatch.setattr("app.services.notifier.urllib.request.urlopen", fake_urlopen)
    assert send_telegram("hi") is True
    assert len(calls) == 3


def test_exhausts_retries_and_raises(monkeypatch):
    monkeypatch.setattr("app.services.notifier.settings.telegram_bot_token", "tok")
    monkeypatch.setattr("app.services.notifier.settings.telegram_chat_id", "123")
    monkeypatch.setattr("app.services.notifier.time.sleep", lambda _s: None)
    calls = []

    def fake_urlopen(_request, timeout=10):
        calls.append(1)
        raise urllib.error.HTTPError("u", 500, "nope", {}, None)

    monkeypatch.setattr("app.services.notifier.urllib.request.urlopen", fake_urlopen)
    with pytest.raises(NotifyError):
        send_telegram("hi", retries=3, backoff=0.0)
    assert len(calls) == 3


def test_network_error_retries_then_raises(monkeypatch):
    monkeypatch.setattr("app.services.notifier.settings.telegram_bot_token", "tok")
    monkeypatch.setattr("app.services.notifier.settings.telegram_chat_id", "123")
    monkeypatch.setattr("app.services.notifier.time.sleep", lambda _s: None)
    calls = []

    def fake_urlopen(_request, timeout=10):
        calls.append(1)
        raise TimeoutError("slow")

    monkeypatch.setattr("app.services.notifier.urllib.request.urlopen", fake_urlopen)
    with pytest.raises(NotifyError):
        send_telegram("hi", retries=2, backoff=0.0)
    assert len(calls) == 2
