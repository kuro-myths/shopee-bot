"""Tests for history pruning."""
from datetime import datetime, timedelta

from app.db import db
from app.services.pruning import prune_history


def _insert_old_point(product_id, days_ago, price):
    ts = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    with db() as conn:
        conn.execute(
            "INSERT INTO price_history (product_id, price, recorded_at) VALUES (?, ?, ?)",
            (product_id, price, ts),
        )


def test_prune_deletes_old_points_keeps_new(client, sample_product):
    client.post("/api/products", json=sample_product)  # product 1, today
    _insert_old_point(1, 120, 50000)
    _insert_old_point(1, 200, 40000)
    # latest point is today's (kept by the MAX(id) rule)

    before = client.get("/api/products/1/history").json()
    assert len(before) == 3

    deleted = prune_history(older_than_days=90)
    assert deleted >= 2

    after = client.get("/api/products/1/history").json()
    assert len(after) == 1  # only today's point remains


def test_prune_nothing_when_recent(client, sample_product):
    client.post("/api/products", json=sample_product)
    deleted = prune_history(older_than_days=90)
    assert deleted == 0
