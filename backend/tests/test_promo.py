"""Tests: Piloterr client, Shopee GraphQL client, promo aggregator + router (network mocked)."""
import hashlib
import io
import json
import urllib.error

import pytest

from app.config import settings
from app.services import piloterr, promo, shopee_graphql
from app.services import errorlog


class FakeResp:
    def __init__(self, body):
        self._b = body if isinstance(body, bytes) else json.dumps(body).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(b"{}"))


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    promo.clear_cache()
    piloterr._spent.update({"day": "", "n": 0})
    monkeypatch.setattr(settings, "piloterr_api_key", "")
    monkeypatch.setattr(settings, "shopee_app_id", "")
    monkeypatch.setattr(settings, "shopee_app_secret", "")
    monkeypatch.setattr(settings, "piloterr_daily_limit", 10)
    errorlog.clear()
    yield
    promo.clear_cache()


# ---------------- Shopee GraphQL ----------------
def test_shopee_auth_header_matches_documented_recipe(monkeypatch):
    monkeypatch.setattr(settings, "shopee_app_id", "123")
    monkeypatch.setattr(settings, "shopee_app_secret", "sekret")
    payload = '{"query":"{x}"}'
    h = shopee_graphql.build_auth_header(payload, 1700000000)
    expected = hashlib.sha256(f"1231700000000{payload}sekret".encode()).hexdigest()
    assert h == f"SHA256 Credential=123, Timestamp=1700000000, Signature={expected}"


def test_shopee_search_offers_parses_nodes(monkeypatch):
    monkeypatch.setattr(settings, "shopee_app_id", "1")
    monkeypatch.setattr(settings, "shopee_app_secret", "s")
    seen = {}

    def fake_open(req, timeout):
        seen["auth"] = req.headers["Authorization"]
        seen["body"] = json.loads(req.data)
        return FakeResp({"data": {"productOfferV2": {"nodes": [{
            "productName": "Earbuds", "price": "300000", "priceMin": "279000", "priceDiscountRate": 20,
            "commissionRate": "0.05", "offerLink": "https://s.shopee.co.id/abc", "imageUrl": "i", "shopName": "Toko",
            "ratingStar": "4.9", "sales": 100}]}}})

    monkeypatch.setattr(shopee_graphql, "_open", fake_open)
    items = shopee_graphql.search_offers('earbuds "bt"', limit=5)
    assert items[0]["price"] == 279000 and items[0]["discount_pct"] == 20
    assert items[0]["commission_pct"] == 5.0 and items[0]["url"].endswith("/abc")
    assert seen["auth"].startswith("SHA256 Credential=1, Timestamp=")
    assert 'keyword:"earbuds \\"bt\\""' in seen["body"]["query"]  # kutip di-escape


def test_shopee_graphql_errors(monkeypatch):
    monkeypatch.setattr(settings, "shopee_app_id", "1")
    monkeypatch.setattr(settings, "shopee_app_secret", "s")
    monkeypatch.setattr(shopee_graphql, "_open", lambda r, t: FakeResp({"errors": [{"message": "Invalid Signature"}]}))
    with pytest.raises(shopee_graphql.ShopeeError, match="Invalid Signature"):
        shopee_graphql.search_offers("x")
    monkeypatch.setattr(shopee_graphql, "_open", lambda r, t: (_ for _ in ()).throw(http_error(500)))
    with pytest.raises(shopee_graphql.ShopeeError, match="HTTP 500"):
        shopee_graphql.search_offers("x")
    assert shopee_graphql.shorten("https://shopee.co.id/x") is None  # gagal -> None


def test_shopee_shorten_via_affiliate_module(monkeypatch):
    from app.services.affiliate import shopee_shorten

    assert shopee_shorten("https://shopee.co.id/x") is None  # belum dikonfigurasi
    monkeypatch.setattr(settings, "shopee_app_id", "1")
    monkeypatch.setattr(settings, "shopee_app_secret", "s")
    monkeypatch.setattr(shopee_graphql, "_open",
                        lambda r, t: FakeResp({"data": {"generateShortLink": {"shortLink": "https://s.shopee.co.id/z"}}}))
    assert shopee_shorten("https://shopee.co.id/x") == "https://s.shopee.co.id/z"


# ---------------- Piloterr ----------------
def test_piloterr_requires_key():
    with pytest.raises(piloterr.PiloterrError) as e:
        piloterr.google_search("x")
    assert e.value.kind == "config"


@pytest.mark.parametrize("code,kind", [(401, "auth"), (402, "credits"), (429, "rate"), (500, "http")])
def test_piloterr_error_mapping(monkeypatch, code, kind):
    monkeypatch.setattr(settings, "piloterr_api_key", "KUNCI-RAHASIA")
    monkeypatch.setattr(piloterr, "_open", lambda r, t: (_ for _ in ()).throw(http_error(code)))
    with pytest.raises(piloterr.PiloterrError) as e:
        piloterr.google_search("x")
    assert e.value.kind == kind and "KUNCI-RAHASIA" not in str(e.value)


def test_piloterr_sends_key_header_and_parses_flexible_shapes(monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "KUNCI")
    seen = {}

    def fake_open(req, timeout):
        seen["key"] = req.headers["X-api-key"]
        seen["url"] = req.full_url
        return FakeResp({"results": [{"title": "Promo A", "link": "https://a", "description": "diskon 30%"}]})

    monkeypatch.setattr(piloterr, "_open", fake_open)
    rows = piloterr.google_search("earbuds")
    assert seen["key"] == "KUNCI" and "/v2/google/search?query=earbuds" in seen["url"]
    assert rows == [{"title": "Promo A", "url": "https://a", "snippet": "diskon 30%"}]
    # bentuk lain: organic_results
    monkeypatch.setattr(piloterr, "_open", lambda r, t: FakeResp({"organic_results": [{"title": "B", "url": "https://b"}]}))
    assert piloterr.google_search("x")[0]["url"] == "https://b"


def test_piloterr_daily_limit_protects_credits(monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "K")
    monkeypatch.setattr(settings, "piloterr_daily_limit", 2)
    monkeypatch.setattr(piloterr, "_open", lambda r, t: FakeResp({"results": []}))
    piloterr.google_search("a")
    piloterr.google_search("b")
    with pytest.raises(piloterr.PiloterrError) as e:
        piloterr.google_search("c")
    assert e.value.kind == "limit"
    assert piloterr.spent_today() == 2


# ---------------- Promo aggregator ----------------
def _add_product(client, name, prices, url):
    for p in prices:
        client.post("/api/products", json={"url": url, "name": name, "marketplace": "shopee", "current_price": p})


def test_tracked_source_finds_price_drops(client):
    _add_product(client, "Redmi Buds 5", [320000, 279000], "https://shopee.co.id/a-i.1.1")
    _add_product(client, "Mouse Naik", [100000, 120000], "https://shopee.co.id/b-i.2.2")
    r = client.get("/api/promos", params={"q": "", "sources": "tracked"}).json()
    titles = [x["title"] for x in r["results"]]
    assert titles == ["Redmi Buds 5"]  # yang harganya naik tidak ikut
    assert r["results"][0]["discount_pct"] == pytest.approx(12.8, abs=0.1)
    assert r["sources"]["tracked"]["status"] == "ok"


def test_unconfigured_sources_are_skipped_with_reason(client):
    r = client.get("/api/promos", params={"q": "earbuds"}).json()
    assert r["sources"]["affiliate"]["status"] == "skipped"
    assert "SHOPEE_APP_ID" in r["sources"]["affiliate"]["message"]
    assert r["sources"]["web"]["status"] == "skipped"
    assert "PILOTERR_API_KEY" in r["sources"]["web"]["message"]


def test_web_source_extracts_discount_and_filters_noise(client, monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "K")
    monkeypatch.setattr(piloterr, "_open", lambda r, t: FakeResp({"results": [
        {"title": "Promo Earbuds diskon hingga 50%", "url": "https://p1", "snippet": "voucher"},
        {"title": "Berita politik", "url": "https://p2", "snippet": "tidak relevan"},
    ]}))
    r = client.get("/api/promos", params={"q": "earbuds", "sources": "web"}).json()
    assert [x["url"] for x in r["results"]] == ["https://p1"]
    assert r["results"][0]["discount_pct"] == 50 and r["results"][0]["source"] == "web"


def test_web_results_are_cached_to_save_credits(client, monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "K")
    calls = []

    def fake_open(req, timeout):
        calls.append(1)
        return FakeResp({"results": [{"title": "Promo diskon 10%", "url": "https://p"}]})

    monkeypatch.setattr(piloterr, "_open", fake_open)
    client.get("/api/promos", params={"q": "tas", "sources": "web"})
    second = client.get("/api/promos", params={"q": "TAS", "sources": "web"}).json()
    assert len(calls) == 1 and second["sources"]["web"]["cached"] is True


def test_source_errors_are_reported_not_raised(client, monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "K")
    monkeypatch.setattr(piloterr, "_open", lambda r, t: (_ for _ in ()).throw(http_error(402)))
    r = client.get("/api/promos", params={"q": "tas", "sources": "web,tracked"})
    assert r.status_code == 200
    assert r.json()["sources"]["web"]["status"] == "error"
    assert "Kredit" in r.json()["sources"]["web"]["message"]
    assert r.json()["sources"]["tracked"]["status"] == "ok"  # sumber lain tetap jalan


def test_results_sorted_by_biggest_discount(client, monkeypatch):
    monkeypatch.setattr(settings, "shopee_app_id", "1")
    monkeypatch.setattr(settings, "shopee_app_secret", "s")
    monkeypatch.setattr(shopee_graphql, "_open", lambda r, t: FakeResp({"data": {"productOfferV2": {"nodes": [
        {"productName": "A", "priceMin": "1", "priceDiscountRate": 10, "offerLink": "u1"},
        {"productName": "B", "priceMin": "1", "priceDiscountRate": 60, "offerLink": "u2"},
    ]}}}))
    r = client.get("/api/promos", params={"q": "earbuds", "sources": "affiliate"}).json()
    assert [x["title"] for x in r["results"]] == ["B", "A"]


def test_status_endpoint_never_leaks_key(client, monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "SANGAT-RAHASIA")
    monkeypatch.setattr(piloterr, "_open", lambda r, t: FakeResp({"credits": 40}))
    body = client.get("/api/promos/status", params={"usage": 1}).text
    assert "SANGAT-RAHASIA" not in body and '"configured":true' in body.replace(" ", "")


def test_promos_require_api_key_when_set(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "rahasia")
    assert client.get("/api/promos").status_code == 401
    assert client.get("/api/promos", headers={"X-API-Key": "rahasia"}).status_code == 200


def test_diagnostics_reports_piloterr_without_leaking(client, monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "RAHASIA-PILOTERR")
    body = client.get("/api/diagnostics")
    assert "RAHASIA-PILOTERR" not in body.text
    ids = {c["id"]: c["status"] for c in body.json()["checks"]}
    assert ids["piloterr"] == "ok"


def test_web_results_with_unsafe_url_are_dropped(client, monkeypatch):
    monkeypatch.setattr(settings, "piloterr_api_key", "K")
    monkeypatch.setattr(piloterr, "_open", lambda r, t: FakeResp({"results": [
        {"title": "Promo diskon 10%", "url": "javascript:alert(1)", "snippet": "promo"},
        {"title": "Promo diskon 20%", "url": "https://aman.example/p", "snippet": "voucher"},
    ]}))
    r = client.get("/api/promos", params={"q": "tas", "sources": "web"}).json()
    assert [x["url"] for x in r["results"]] == ["https://aman.example/p"]
