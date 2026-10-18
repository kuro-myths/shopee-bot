"""Tests for statistics, dedupe and notes."""
def test_stats_endpoint(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["price_points"] == 1
    assert body["marketplaces"] == {"shopee": 1}


def test_stats_empty(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_stats_counts_targets(client, sample_product):
    client.post("/api/products", json=sample_product)
    client.put("/api/products/1/target", json={"target_price": 50000})
    res = client.get("/api/stats")
    assert res.json()["with_target"] == 1


def test_identical_price_is_deduped(client, sample_product):
    client.post("/api/products", json=sample_product)  # 100000
    client.post("/api/products", json={**sample_product, "current_price": 100000})
    res = client.get("/api/products/1/history")
    assert len(res.json()) == 1  # second identical point skipped


def test_different_price_not_deduped(client, sample_product):
    client.post("/api/products", json=sample_product)  # 100000
    client.post("/api/products", json={**sample_product, "current_price": 110000})
    res = client.get("/api/products/1/history")
    assert len(res.json()) == 2


def test_set_note(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.put("/api/products/1/note", json={"note": "kado ulang tahun"})
    assert res.status_code == 200
    assert res.json()["note"] == "kado ulang tahun"


def test_set_note_404(client):
    res = client.put("/api/products/999/note", json={"note": "x"})
    assert res.status_code == 404
