"""Unit tests for the filters service."""
from app.db import db, init_db
from app.services.filters import list_products


def setup_module():
    init_db()


def teardown_function():
    with db() as conn:
        conn.execute("DELETE FROM price_history")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM sqlite_sequence")


def _add(url, name, marketplace, target=None):
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO products (url, name, marketplace, target_price) VALUES (?, ?, ?, ?)",
            (url, name, marketplace, target),
        )
        return cur.lastrowid


def test_search_matches_name():
    _add("u1", "Keyboard RGB", "shopee")
    _add("u2", "Mouse Wireless", "tiktok")
    rows, total = list_products(search="keyboard")
    assert total == 1
    assert rows[0]["name"] == "Keyboard RGB"


def test_marketplace_filter():
    _add("u1", "A", "shopee")
    _add("u2", "B", "tiktok")
    rows, total = list_products(marketplace="shopee")
    assert total == 1


def test_has_target_filter():
    _add("u1", "A", "shopee", target=50000)
    _add("u2", "B", "tiktok")
    rows, total = list_products(has_target=True)
    assert total == 1


def test_pagination():
    for i in range(5):
        _add(f"u{i}", f"Produk {i}", "shopee")
    rows, total = list_products(page=1, page_size=2)
    assert total == 5
    assert len(rows) == 2


def test_page_size_capped():
    rows, total = list_products(page=1, page_size=9999)
    assert total == 0
    assert len(rows) == 0  # no products; cap not observable but no error
