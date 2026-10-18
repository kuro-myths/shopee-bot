"""Unit tests for the price drop detection logic."""
from app.config import settings
from app.services.detector import check_drop, describe_drop


def test_drop_above_threshold_is_detected():
    is_drop, pct = check_drop(100000, 90000)
    assert is_drop is True
    assert pct == -10.0


def test_small_drop_below_threshold_is_not_detected():
    is_drop, pct = check_drop(100000, 97000)
    assert is_drop is False
    assert pct == -3.0


def test_price_increase_is_not_a_drop():
    is_drop, _ = check_drop(80000, 120000)
    assert is_drop is False


def test_unchanged_price_is_not_a_drop():
    is_drop, _ = check_drop(80000, 80000)
    assert is_drop is False


def test_new_product_without_previous_min_is_not_a_drop():
    is_drop, _ = check_drop(None, 50000)
    assert is_drop is False


def test_threshold_is_configurable():
    original = settings.drop_threshold_pct
    try:
        settings.drop_threshold_pct = 1
        is_drop, _ = check_drop(100000, 98500)  # -1.5% crosses the 1% threshold
        assert is_drop is True
        is_drop, _ = check_drop(100000, 99500)  # -0.5% stays below it
        assert is_drop is False
    finally:
        settings.drop_threshold_pct = original


def test_describe_drop_contains_product_details():
    product = {"name": "Keyboard", "marketplace": "shopee", "url": "https://example.com"}
    msg = describe_drop(product, 90000, -10.0)
    assert "Keyboard" in msg
    assert "shopee" in msg
    assert "90,000" in msg
