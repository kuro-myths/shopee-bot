"""Tests for the notification cooldown."""
from app.services.cooldown import is_on_cooldown, mark_sent, reset, should_notify


def setup_function():
    reset()


def test_first_notify_allowed():
    assert should_notify(1) is True


def test_second_notify_blocked():
    should_notify(1)
    assert should_notify(1) is False


def test_different_products_independent():
    should_notify(1)
    assert should_notify(2) is True


def test_mark_sent_then_cooldown():
    mark_sent(5)
    assert is_on_cooldown(5) is True
