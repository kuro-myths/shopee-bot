"""Unit tests for the target service."""
from app.services.targets import check_target_reached, describe_target_reached


def test_reached_when_equal():
    assert check_target_reached(50000, 50000) is True


def test_reached_when_below():
    assert check_target_reached(50000, 45000) is True


def test_not_reached_when_above():
    assert check_target_reached(50000, 55000) is False


def test_no_target():
    assert check_target_reached(None, 45000) is False


def test_no_price():
    assert check_target_reached(50000, None) is False


def test_describe_contains_fields():
    msg = describe_target_reached({"name": "X", "marketplace": "shopee", "url": "u"}, 45000, 50000)
    assert "X" in msg
    assert "45,000" in msg
    assert "50,000" in msg
