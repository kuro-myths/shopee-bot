"""Tests for product archiving."""
def test_archive_excludes_from_listing(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.post("/api/products/1/archive")
    assert res.status_code == 200
    listing = client.get("/api/products").json()
    assert listing["total"] == 0


def test_restore_returns_to_listing(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.post("/api/products/1/archive")
    res = client.post("/api/products/1/restore")
    assert res.status_code == 200
    listing = client.get("/api/products").json()
    assert listing["total"] == 1


def test_archive_preserves_history(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.post("/api/products/1/archive")
    res = client.get("/api/products/1/history")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_archive_404(client):
    res = client.post("/api/products/999/archive")
    assert res.status_code == 404


def test_product_out_has_archived_flag(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products/1")
    assert res.json()["archived"] is False
