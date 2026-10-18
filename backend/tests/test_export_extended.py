"""Tests for the export helpers (active filter + extended columns)."""
import json

from app.services.export import active_products, to_csv, to_json


def _row(**overrides):
    base = {
        "id": 1,
        "name": "Produk A",
        "marketplace": "shopee",
        "url": "https://shopee.co.id/x-i.1.2",
        "current_price": 90000,
        "min_price": 85000,
        "max_price": 100000,
        "target_price": None,
        "note": "",
        "archived": 0,
        "created_at": "2026-01-01 10:00:00",
        "updated_at": "2026-01-02 10:00:00",
    }
    base.update(overrides)
    return base


def test_active_products_filters_archived():
    rows = [
        _row(id=1),
        _row(id=2, archived=1),
        _row(id=3, archived=1),
    ]
    active = active_products(rows)
    assert [r["id"] for r in active] == [1]


def test_to_csv_includes_note_column():
    csv_out = to_csv([_row(note="diskon gajian")])
    header = csv_out.splitlines()[0]
    assert "note" in header
    assert "diskon gajian" in csv_out


def test_to_json_includes_note_and_skips_archived():
    rows = [_row(note="wishlist"), _row(id=2, archived=1)]
    payload = json.loads(to_json(active_products(rows)))
    assert len(payload) == 1
    assert payload[0]["note"] == "wishlist"
    assert "archived" not in payload[0]


def test_empty_csv_header():
    header = to_csv([]).splitlines()[0]
    assert header.startswith("id,name,marketplace")
    assert "note" in header
