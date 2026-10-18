"""Tests for the history summary endpoint."""
def test_summary_computes_stats(client, sample_product):
    for price in (100000, 120000, 80000):
        client.post("/api/products", json={**sample_product, "current_price": price})
    res = client.get("/api/products/1/summary")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 3
    assert body["min"] == 80000
    assert body["max"] == 120000
    assert body["avg"] == 100000


def test_summary_empty_history(client, sample_product):
    no_price = {k: v for k, v in sample_product.items() if k != "current_price"}
    client.post("/api/products", json=no_price)
    res = client.get("/api/products/1/summary")
    assert res.status_code == 200
    assert res.json()["count"] == 0
    assert res.json()["min"] is None


def test_summary_404(client):
    res = client.get("/api/products/999/summary")
    assert res.status_code == 404
