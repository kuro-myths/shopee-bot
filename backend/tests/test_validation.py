"""Tests for API input validation."""
def test_invalid_target_rejected(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.put("/api/products/1/target", json={"target_price": -5})
    assert res.status_code == 422


def test_missing_url_rejected(client):
    res = client.post("/api/products", json={"name": "No URL"})
    assert res.status_code == 422


def test_empty_name_defaults(client):
    res = client.post("/api/products", json={"url": "https://shopee.co.id/x-i.1.1"})
    assert res.status_code == 200
    assert res.json()["name"] == "Untitled product"


def test_negative_price_rejected(client, sample_product):
    res = client.post("/api/products", json={**sample_product, "current_price": -100})
    assert res.status_code == 422


def test_history_limit_bounds(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products/1/history", params={"limit": 0})
    assert res.status_code == 422
    res = client.get("/api/products/1/history", params={"limit": 99999})
    assert res.status_code == 422
