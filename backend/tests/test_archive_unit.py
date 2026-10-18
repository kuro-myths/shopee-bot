"""Unit tests for the archive service (direct, no HTTP)."""
from app.db import db, init_db
from app.services.archive import archive_product, restore_product


def setup_module():
    init_db()


def teardown_function():
    with db() as conn:
        conn.execute("DELETE FROM price_history")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM sqlite_sequence")


def _add_product():
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO products (url, name, marketplace) VALUES (?, ?, ?)",
            ("https://tiktok.com/shop/u", "B", "tiktok"),
        )
        return cur.lastrowid


def test_archive_marks_flag():
    pid = _add_product()
    assert archive_product(pid) is True
    with db() as conn:
        row = conn.execute("SELECT archived FROM products WHERE id=?", (pid,)).fetchone()
    assert row["archived"] == 1


def test_archive_missing_product():
    assert archive_product(999999) is False


def test_restore_clears_flag():
    pid = _add_product()
    archive_product(pid)
    assert restore_product(pid) is True
    with db() as conn:
        row = conn.execute("SELECT archived FROM products WHERE id=?", (pid,)).fetchone()
    assert row["archived"] == 0


def test_restore_non_archived_is_false():
    pid = _add_product()
    assert restore_product(pid) is False
