"""Tests for the history limit parameter."""
def test_history_limit(client, sample_product):
    for i in range(5):
        client.post("/api/products", json={
            **sample_product,
            "current_price": 100000 + i * 1000,
        })
    res = client.get("/api/products/1/history", params={"limit": 2})
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2
    # Most recent two prices, in ascending order
    assert history[-1]["price"] == 104000.0


def test_history_default_limit(client, sample_product):
    for i in range(3):
        client.post("/api/products", json={
            **sample_product,
            "current_price": 100000 + i * 1000,
        })
    res = client.get("/api/products/1/history")
    assert len(res.json()) == 3
