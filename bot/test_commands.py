"""Unit tests for the bot command handlers."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from commands import (  # noqa: E402
    cmd_list,
    cmd_recent,
    cmd_settings,
    cmd_stats,
    cmd_start,
    cmd_top,
    parse_target_arg,
)


def test_cmd_start_lists_commands():
    text = cmd_start()
    assert "/track" in text
    assert "/stats" in text
    assert "/export" in text
    assert "/settings" in text
    assert "/menu" in text


def test_cmd_settings_reflects_alerts_state():
    out = cmd_settings(True, "http://localhost:8000")
    assert "AKTIF" in out
    assert "http://localhost:8000" in out
    assert "NONAKTIF" in cmd_settings(False, "http://localhost:8000")


def test_cmd_list_empty():
    assert "Belum ada produk" in cmd_list([])


def test_cmd_list_formats_prices():
    products = [{"id": 1, "name": "Keyboard", "marketplace": "shopee",
                 "current_price": 100000, "min_price": 90000}]
    text = cmd_list(products)
    assert "#1" in text
    assert "Keyboard" in text
    assert "Rp 100,000" in text


def test_cmd_stats_counts():
    products = [
        {"marketplace": "shopee", "target_price": 50000, "current_price": 40000, "min_price": 60000},
        {"marketplace": "tiktok", "target_price": None, "current_price": 20000, "min_price": 20000},
    ]
    text = cmd_stats(products)
    assert "Total produk: 2" in text
    assert "Produk dengan target: 1" in text
    assert "Harga di bawah minimum: 1" in text


def test_parse_target_arg():
    assert parse_target_arg("3 45000") == (3, 45000.0)
    assert parse_target_arg("12 1.500.000") == (12, 1500000.0)
    assert parse_target_arg("abc") is None


def test_cmd_top_ranks_by_discount():
    products = [
        {"id": 1, "name": "A", "current_price": 80000, "min_price": 100000},
        {"id": 2, "name": "B", "current_price": 95000, "min_price": 100000},
    ]
    text = cmd_top(products)
    assert text.index("#1") < text.index("#2")


def test_cmd_top_empty():
    assert "Belum ada produk" in cmd_top([])


def test_cmd_recent_orders_by_update():
    products = [
        {"id": 1, "name": "A", "updated_at": "2026-01-01", "current_price": 100},
        {"id": 2, "name": "B", "updated_at": "2026-02-01", "current_price": 200},
    ]
    text = cmd_recent(products)
    assert text.index("#2") < text.index("#1")
