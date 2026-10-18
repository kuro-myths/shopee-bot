"""Unit tests for the dedupe service (direct, no HTTP)."""
from app.db import db, init_db
from app.services.dedupe import should_record


def setup_module():
    init_db()
    # Start from a clean slate even if other modules left rows behind
    with db() as conn:
        conn.execute("DELETE FROM price_history")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM sqlite_sequence")


def teardown_function():
    with db() as conn:
        conn.execute("DELETE FROM price_history")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM sqlite_sequence")


import uuid


def _add_product():
    """Insert a product with a unique URL (other test modules may leave rows)."""
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO products (url, name, marketplace) VALUES (?, ?, ?)",
            (f"https://shopee.co.id/u-{uuid.uuid4().hex}.1", "A", "shopee"),
        )
        return cur.lastrowid


def test_first_point_always_recorded():
    pid = _add_product()
    assert should_record(pid, 100000) is True


def test_same_price_recently_is_skipped():
    pid = _add_product()
    with db() as conn:
        conn.execute(
            "INSERT INTO price_history (product_id, price) VALUES (?, ?)", (pid, 100000)
        )
    assert should_record(pid, 100000) is False


def test_different_price_recorded():
    pid = _add_product()
    with db() as conn:
        conn.execute(
            "INSERT INTO price_history (product_id, price) VALUES (?, ?)", (pid, 100000)
        )
    assert should_record(pid, 100001) is True


def test_no_product_returns_true():
    # Unknown product id -> no history -> record allowed
    assert should_record(999999, 100000) is True
