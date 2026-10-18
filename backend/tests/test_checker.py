"""Tests for the background price checker."""
from app.services.checker import PriceChecker


def test_checker_starts_and_stops():
    checker = PriceChecker(interval_seconds=3600)
    checker.start()
    assert checker._thread is not None
    assert checker._thread.is_alive()
    checker.stop()
    assert not checker._thread.is_alive()


def test_checker_no_products_returns_zero(client):
    checker = PriceChecker(interval_seconds=3600)
    assert checker.check_all() == 0


def test_checker_stop_is_idempotent():
    checker = PriceChecker(interval_seconds=3600)
    checker.start()
    checker.stop()
    checker.stop()  # must not raise
