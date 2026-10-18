"""Tests for the price target / wishlist feature."""
import pytest


def test_set_target(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.put("/api/products/1/target", json={"target_price": 50000})
    assert res.status_code == 200
    body = res.json()
    assert body["target_price"] == 50000
    assert body["target_reached"] is False


def test_target_reached_after_price_drop(client, sample_product):
    client.post("/api/products", json=sample_product)  # 100000
    client.put("/api/products/1/target", json={"target_price": 90000})
    # Drop to 85000 — below the 90000 target
    res = client.post("/api/products", json={**sample_product, "current_price": 85000})
    assert res.status_code == 200
    assert res.json()["target_reached"] is True


def test_clear_target(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.put("/api/products/1/target", json={"target_price": 50000})
    res = client.delete("/api/products/1/target")
    assert res.status_code == 200
    assert res.json()["target_price"] is None


def test_set_target_requires_positive_price(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.put("/api/products/1/target", json={"target_price": 0})
    assert res.status_code == 422


def test_set_target_404(client):
    res = client.put("/api/products/999/target", json={"target_price": 50000})
    assert res.status_code == 404


def test_target_included_in_product_listing(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.put("/api/products/1/target", json={"target_price": 50000})
    res = client.get("/api/products")
    assert res.json()["products"][0]["target_price"] == 50000
