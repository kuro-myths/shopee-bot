"""Integration tests for the products API."""
import pytest


def test_create_product(client, sample_product):
    res = client.post("/api/products", json=sample_product)
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 1
    assert body["name"] == sample_product["name"]
    assert body["current_price"] == 100000
    assert body["min_price"] == 100000


def test_upsert_same_url_updates_existing(client, sample_product):
    client.post("/api/products", json=sample_product)
    update = {**sample_product, "name": "Nama Baru", "current_price": 120000}
    res = client.post("/api/products", json=update)
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 1
    assert body["name"] == "Nama Baru"
    assert body["current_price"] == 120000
    assert body["min_price"] == 100000  # all-time min preserved
    assert body["max_price"] == 120000


def test_price_history_is_recorded(client, sample_product):
    for price in (100000, 120000, 80000):
        client.post("/api/products", json={**sample_product, "current_price": price})
    res = client.get("/api/products/1/history")
    assert res.status_code == 200
    history = res.json()
    assert [h["price"] for h in history] == [100000.0, 120000.0, 80000.0]


def test_list_products(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products")
    assert res.status_code == 200
    assert len(res.json()["products"]) == 1


def test_get_product_404(client):
    res = client.get("/api/products/999")
    assert res.status_code == 404


def test_delete_product(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.delete("/api/products/1")
    assert res.status_code == 200
    assert res.json() == {"deleted": 1}


def test_delete_product_404(client):
    res = client.delete("/api/products/999")
    assert res.status_code == 404


def test_affiliate_endpoint_returns_fallback(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.post("/api/products/1/affiliate")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "original"
    assert body["url"] == sample_product["url"]


def test_affiliate_endpoint_404(client):
    res = client.post("/api/products/999/affiliate")
    assert res.status_code == 404


def test_product_without_price_has_no_history(client, sample_product):
    no_price = {k: v for k, v in sample_product.items() if k != "current_price"}
    res = client.post("/api/products", json=no_price)
    assert res.status_code == 200
    assert res.json()["current_price"] is None
