"""Unit tests for export helpers (no HTTP)."""
import json

from app.services.export import to_csv, to_json


def _row(**overrides):
    base = {
        "id": 1, "name": "Produk", "marketplace": "shopee", "url": "https://x",
        "current_price": 100.0, "min_price": 90.0, "max_price": 120.0,
        "target_price": None, "created_at": "2026-01-01", "updated_at": "2026-01-02",
    }
    base.update(overrides)
    return base


def test_to_csv_has_header():
    text = to_csv([_row()])
    assert text.splitlines()[0].startswith("id,name,marketplace")


def test_to_csv_quotes_names():
    text = to_csv([_row(name="Produk, Keren")])
    assert '"Produk, Keren"' in text


def test_to_json_is_valid():
    text = to_json([_row()])
    data = json.loads(text)
    assert data[0]["name"] == "Produk"


def test_to_json_empty_list():
    assert json.loads(to_json([])) == []


def test_to_csv_empty_list_returns_header_only():
    text = to_csv([])
    assert len(text.splitlines()) == 1
