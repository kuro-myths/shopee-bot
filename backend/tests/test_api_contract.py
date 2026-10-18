"""Tests for the API response contract (fields consumers rely on)."""
EXPECTED_FIELDS = {
    "id", "url", "name", "marketplace", "image", "current_price",
    "min_price", "max_price", "target_price", "target_reached",
    "note", "archived", "created_at", "updated_at",
}


def test_product_out_has_all_consumer_fields(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products/1")
    assert EXPECTED_FIELDS.issubset(set(res.json().keys()))


def test_listing_envelope(client, sample_product):
    client.post("/api/products", json=sample_product)
    body = client.get("/api/products").json()
    assert {"products", "total", "page", "page_size"}.issubset(set(body.keys()))


def test_affiliate_contract(client, sample_product):
    client.post("/api/products", json=sample_product)
    body = client.post("/api/products/1/affiliate").json()
    assert {"url", "source", "note"}.issubset(set(body.keys()))


def test_history_point_contract(client, sample_product):
    client.post("/api/products", json=sample_product)
    point = client.get("/api/products/1/history").json()[0]
    assert {"price", "date"}.issubset(set(point.keys()))


def test_health_contract(client):
    body = client.get("/health").json()
    assert {"status", "database", "uptime_seconds", "products_tracked"}.issubset(set(body.keys()))


def test_pagination_fields(client, sample_product):
    client.post("/api/products", json=sample_product)
    body = client.get("/api/products").json()
    assert body["pages"] == 1
    assert body["has_next"] is False
    assert body["has_prev"] is False
