"""Tests for the export endpoints."""
import json


def test_export_csv(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products/export/csv")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "Contoh Produk" in res.text
    assert "marketplace" in res.text


def test_export_json(client, sample_product):
    client.post("/api/products", json=sample_product)
    res = client.get("/api/products/export/json")
    assert res.status_code == 200
    data = json.loads(res.text)
    assert len(data) == 1
    assert data[0]["name"] == "Contoh Produk"


def test_export_empty_csv(client):
    res = client.get("/api/products/export/csv")
    assert res.status_code == 200
    assert "id,name" in res.text


def test_export_invalid_format(client):
    res = client.get("/api/products/export/xml")
    assert res.status_code == 400
