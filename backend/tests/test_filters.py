"""Tests for search, filtering and pagination."""
def test_list_returns_paginated_envelope(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert len(body["products"]) == 1


def test_search_by_name(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products", params={"search": "Contoh"})
    assert res.json()["total"] == 1
    res = client.get("/api/products", params={"search": "Tidakada"})
    assert res.json()["total"] == 0


def test_filter_by_marketplace(client, sample_product):
    client.post("/api/products", json=sample_product)
    tiktok = {**sample_product, "url": "https://tiktok.com/shop/y", "marketplace": "tiktok"}
    client.post("/api/products", json=tiktok)
    res = client.get("/api/products", params={"marketplace": "tiktok"})
    body = res.json()
    assert body["total"] == 1
    assert body["products"][0]["marketplace"] == "tiktok"


def test_filter_has_target(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.put("/api/products/1/target", json={"target_price": 40000})
    res = client.get("/api/products", params={"has_target": "true"})
    assert res.json()["total"] == 1


def test_pagination(client, sample_product):
    for i in range(3):
        client.post("/api/products", json={
            **sample_product,
            "url": f"https://shopee.co.id/p{i}-i.1.1",
            "name": f"Produk {i}",
        })
    res = client.get("/api/products", params={"page": 1, "page_size": 2})
    assert res.json()["total"] == 3
    assert len(res.json()["products"]) == 2
