"""Tests for the per-chat state store."""
import os
import tempfile

os.environ["BOT_STATE_FILE"] = os.path.join(tempfile.mkdtemp(), "state.json")

from state import alerts_enabled, set_alerts  # noqa: E402


def test_alerts_default_on():
    assert alerts_enabled(12345) is True


def test_toggle_off():
    set_alerts(12345, False)
    assert alerts_enabled(12345) is False


def test_toggle_back_on():
    set_alerts(12345, True)
    assert alerts_enabled(12345) is True


def test_state_is_per_chat():
    set_alerts(111, False)
    assert alerts_enabled(222) is True
