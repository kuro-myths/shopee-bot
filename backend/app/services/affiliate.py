"""Affiliate link generation.

Shopee (AMS Open API) and TikTok Shop (Partner Center) both offer
official affiliate APIs. The implementations below follow their public
API shapes; credentials come from the environment. When credentials are
not configured, the original product URL is returned unchanged so the
pipeline keeps working during development.

NOTE: Both APIs require signed requests (HMAC-SHA256 with app secret).
Endpoint paths and field names follow the published docs; adjust to the
exact response envelope if the platform version changes.
"""
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request

from ..config import settings

# --------------------------------------------------------------------------
# Shopee Affiliate Marketing Solutions (AMS) — Open API
# --------------------------------------------------------------------------


def _shopee_sign(partner_id, path, timestamp):
    base = f"{partner_id}{path}{timestamp}"
    return hmac.new(
        settings.shopee_app_secret.encode(), base.encode(), hashlib.sha256
    ).hexdigest()


def shopee_shorten(product_url: str):
    """Shorten a product URL through the Shopee AMS Open API.

    Returns the affiliate URL or None on failure/missing config.
    """
    if not (settings.shopee_app_id and settings.shopee_app_secret and settings.shopee_partner_id):
        return None

    path = "/api/v2/shortlink/generate"
    timestamp = int(time.time())
    sign = _shopee_sign(settings.shopee_partner_id, path, timestamp)

    url = (
        "https://open-api.affiliate.shopee.co.id"
        f"{path}?partner_id={settings.shopee_partner_id}"
        f"&timestamp={timestamp}&sign={sign}&app_id={settings.shopee_app_id}"
    )
    body = json.dumps({"raw_url": product_url}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            # response envelope: {"data": {"short_url": "..."}, "status": 200}
            short = (data.get("data") or {}).get("short_url")
            return short if short else None
    except Exception:
        return None


# --------------------------------------------------------------------------
# TikTok Shop Affiliate API (Partner Center)
# --------------------------------------------------------------------------


def _tiktok_sign(secret, timestamp):
    return hmac.new(secret.encode(), str(timestamp).encode(), hashlib.sha256).hexdigest()


def tiktok_affiliate(product_url: str):
    """Generate an affiliate link through TikTok Shop's Affiliate API.

    TikTok's affiliate program is deeply tied to the in-app creator
    flow. This mirrors the documented affiliate-link endpoint; returns
    None when credentials are missing or the call fails.
    """
    if not (settings.tiktok_app_key and settings.tiktok_app_secret and settings.tiktok_shop_id):
        return None

    # Endpoint per TikTok Shop Partner Center docs (Affiliate Marketing API)
    url = "https://open-api.tiktokglobalshop.com/api/affiliate/link/generate"
    timestamp = str(int(time.time()))
    sign = _tiktok_sign(settings.tiktok_app_secret, timestamp)

    body = json.dumps({
        "shop_id": settings.tiktok_shop_id,
        "product_url": product_url,
        "timestamp": timestamp,
        "sign": sign,
        "app_key": settings.tiktok_app_key,
    }).encode()

    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            link = (data.get("data") or {}).get("link")
            return link if link else None
    except Exception:
        return None


# --------------------------------------------------------------------------
# Facade used by the router
# --------------------------------------------------------------------------


def _field(row, key, default=None):
    """Read a field from either a dict or a sqlite3.Row safely."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def get_affiliate_url(product) -> dict:
    """Return an affiliate URL for a product row (dict or sqlite3.Row)."""
    marketplace = _field(product, "marketplace")
    url = _field(product, "url")
    name = _field(product, "name") or ""

    if marketplace == "shopee":
        short = shopee_shorten(url)
        if short:
            return {
                "url": short,
                "source": "shopee_api",
                "product": name,
                "note": "Short link dari Shopee AMS Open API",
            }
    elif marketplace == "tiktok":
        link = tiktok_affiliate(url)
        if link:
            return {
                "url": link,
                "source": "tiktok_api",
                "product": name,
                "note": "Affiliate link dari TikTok Shop Partner API",
            }

    return {
        "url": url,
        "source": "original",
        "product": name,
        "note": "API affiliate belum dikonfigurasi — pakai URL produk asli. "
               "Set SHOPEE_APP_ID/SECRET atau TIKTOK_APP_KEY/SECRET di .env.",
    }
