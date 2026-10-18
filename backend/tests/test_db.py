"""Unit tests for the database layer."""
from app.db import db, init_db


def test_init_db_creates_tables():
    init_db()
    with db() as conn:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert "products" in tables
    assert "price_history" in tables


def test_product_insert_and_read():
    init_db()
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO products (url, name, marketplace) VALUES (?, ?, ?)",
            ("https://tiktok.com/shop/x", "Produk TikTok", "tiktok"),
        )
        product_id = cur.lastrowid
        row = conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
    assert row["name"] == "Produk TikTok"
    assert row["marketplace"] == "tiktok"


def test_url_is_unique():
    init_db()
    with db() as conn:
        conn.execute(
            "INSERT INTO products (url, name, marketplace) VALUES (?, ?, ?)",
            ("https://shopee.co.id/u-i.1.1", "A", "shopee"),
        )
        with conn:
            try:
                conn.execute(
                    "INSERT INTO products (url, name, marketplace) VALUES (?, ?, ?)",
                    ("https://shopee.co.id/u-i.1.1", "B", "shopee"),
                )
                raised = False
            except Exception:
                raised = True
    assert raised is True
