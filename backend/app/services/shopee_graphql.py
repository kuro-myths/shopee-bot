"""Klien Shopee Affiliate Open API (GraphQL).

Autentikasi (sesuai dokumentasi Shopee Affiliate): header

    Authorization: SHA256 Credential=<AppId>, Timestamp=<ts>, Signature=<sig>

dengan sig = SHA256(AppId + Timestamp + Payload + Secret) (hex), Payload = body
JSON persis seperti yang dikirim. Kredensial (App ID + Secret) gratis, didapat
dari panel Open API di portal affiliate Shopee setelah akun disetujui.
"""
import hashlib
import json
import time
import urllib.error
import urllib.request

from ..config import settings

GRAPHQL_URL = "https://open-api.affiliate.shopee.co.id/graphql"
TIMEOUT = 15

# sortType produk: 1=relevansi, 2=terlaris, 3=harga tertinggi, 4=harga terendah, 5=komisi tertinggi
SORT_RELEVANCE, SORT_SALES, SORT_PRICE_DESC, SORT_PRICE_ASC, SORT_COMMISSION = 1, 2, 3, 4, 5


class ShopeeError(Exception):
    pass


def configured() -> bool:
    return bool(settings.shopee_app_id and settings.shopee_app_secret)


def build_auth_header(payload: str, timestamp: int) -> str:
    raw = f"{settings.shopee_app_id}{timestamp}{payload}{settings.shopee_app_secret}"
    sig = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"SHA256 Credential={settings.shopee_app_id}, Timestamp={timestamp}, Signature={sig}"


def _open(req, timeout):  # dipisah agar mudah di-mock pada tes
    return urllib.request.urlopen(req, timeout=timeout)


def graphql(query: str) -> dict:
    if not configured():
        raise ShopeeError("SHOPEE_APP_ID / SHOPEE_APP_SECRET belum diisi")
    payload = json.dumps({"query": query}, separators=(",", ":"))
    ts = int(time.time())
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": build_auth_header(payload, ts)},
    )
    try:
        with _open(req, TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ShopeeError(f"HTTP {exc.code} dari Shopee Affiliate API") from None
    except Exception as exc:
        raise ShopeeError(f"Tidak bisa menghubungi Shopee Affiliate API: {type(exc).__name__}") from None
    if data.get("errors"):
        first = data["errors"][0]
        raise ShopeeError(str(first.get("message") or first)[:200])
    return data.get("data") or {}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _pct(v):
    """commissionRate dikirim sebagai pecahan (0.05 = 5%); jaga-jaga jika sudah persen."""
    x = _num(v)
    if x is None:
        return None
    return round(x * 100, 2) if x <= 1 else x


def search_offers(keyword: str, limit: int = 10, sort: int = SORT_SALES) -> list:
    """Cari produk ber-diskon/komisi lewat productOfferV2."""
    kw = json.dumps(keyword)  # kutip + escape aman untuk literal GraphQL
    q = (
        "{productOfferV2(keyword:%s,sortType:%d,page:1,limit:%d){nodes{"
        "itemId productName price priceMin priceMax priceDiscountRate commissionRate "
        "imageUrl shopName productLink offerLink ratingStar sales}}}" % (kw, int(sort), int(limit))
    )
    nodes = ((graphql(q).get("productOfferV2") or {}).get("nodes")) or []
    out = []
    for n in nodes:
        price = _num(n.get("priceMin")) or _num(n.get("price"))
        out.append({
            "title": n.get("productName") or "",
            "url": n.get("offerLink") or n.get("productLink") or "",
            "price": price,
            "discount_pct": _num(n.get("priceDiscountRate")),
            "commission_pct": _pct(n.get("commissionRate")),
            "image": n.get("imageUrl") or "",
            "shop": n.get("shopName") or "",
            "rating": _num(n.get("ratingStar")),
            "sold": n.get("sales"),
        })
    return out


def shorten(url: str, sub_ids=None):
    """Buat link affiliate pendek (generateShortLink). None jika gagal."""
    subs = json.dumps(list(sub_ids or []))
    q = "mutation{generateShortLink(input:{originUrl:%s,subIds:%s}){shortLink}}" % (json.dumps(url), subs)
    try:
        link = (graphql(q).get("generateShortLink") or {}).get("shortLink")
    except ShopeeError:
        return None
    return link or None
