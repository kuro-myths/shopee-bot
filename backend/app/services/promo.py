"""Agregator promo/diskon dari beberapa sumber.

Sumber:
  tracked    - produk yang Anda pantau yang harganya turun (gratis, selalu ada)
  affiliate  - Shopee Affiliate Open API: produk diskon + komisi (gratis, perlu App ID/Secret)
  web        - pencarian web promo/voucher via Piloterr (kredit terbatas, di-cache)
"""
import re
import time

from ..config import settings
from ..db import db
from . import piloterr, shopee_graphql

SOURCES = ("tracked", "affiliate", "web")
_cache: dict = {}
_PCT = re.compile(r"(\d{1,2})\s?%")
_PROMO_WORDS = ("diskon", "promo", "voucher", "kupon", "cashback", "gratis ongkir", "flash sale")


def clear_cache():
    _cache.clear()


def _cached(key, producer):
    ttl = settings.promo_cache_seconds
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1], True
    value = producer()
    _cache[key] = (time.time(), value)
    return value, False


def search_tracked(q: str = "") -> list:
    like = f"%{q.strip()}%"
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE archived = 0 AND name LIKE ?", (like,)
        ).fetchall()
    out = []
    for r in rows:
        cur, top = r["current_price"], r["max_price"]
        if not cur or not top or cur >= top:
            continue
        pct = round((top - cur) / top * 100, 1)
        reached = r["target_price"] is not None and cur <= r["target_price"]
        out.append({
            "title": r["name"], "url": r["url"], "price": cur, "original_price": top,
            "discount_pct": pct, "image": r["image"] or "", "shop": r["marketplace"],
            "note": "Mencapai harga target Anda" if reached else "Harga turun dari tertinggi yang tercatat",
        })
    out.sort(key=lambda d: d["discount_pct"], reverse=True)
    return out


def search_affiliate(q: str, limit: int = 10) -> list:
    return shopee_graphql.search_offers(q, limit=limit)


def search_web(q: str, limit: int = 8) -> list:
    rows = piloterr.google_search(f"promo diskon voucher {q} shopee", limit=limit)
    out = []
    for r in rows:
        if not r["url"].lower().startswith(("http://", "https://")):
            continue  # buang skema berbahaya (javascript:, data:, ...)
        text = f"{r['title']} {r['snippet']}"
        low = text.lower()
        if not any(w in low for w in _PROMO_WORDS):
            continue
        pcts = [int(x) for x in _PCT.findall(text)]
        out.append({
            "title": r["title"], "url": r["url"], "price": None,
            "discount_pct": max(pcts) if pcts else None,
            "note": r["snippet"][:200],
        })
    return out


def search(q: str, sources=None) -> dict:
    q = (q or "").strip()
    wanted = [s for s in (sources or SOURCES) if s in SOURCES]
    results, status = [], {}

    for name in wanted:
        try:
            if name == "tracked":
                items, hit = search_tracked(q), False
            elif name == "affiliate":
                if not shopee_graphql.configured():
                    status[name] = {"status": "skipped", "count": 0, "message": "SHOPEE_APP_ID/SECRET belum diisi"}
                    continue
                if len(q) < 2:
                    status[name] = {"status": "skipped", "count": 0, "message": "Isi kata kunci (min 2 huruf)"}
                    continue
                items, hit = _cached(("affiliate", q.lower()), lambda: search_affiliate(q))
            else:  # web
                if not piloterr.configured():
                    status[name] = {"status": "skipped", "count": 0, "message": "PILOTERR_API_KEY belum diisi"}
                    continue
                if len(q) < 2:
                    status[name] = {"status": "skipped", "count": 0, "message": "Isi kata kunci (min 2 huruf)"}
                    continue
                items, hit = _cached(("web", q.lower()), lambda: search_web(q))
        except (piloterr.PiloterrError, shopee_graphql.ShopeeError) as exc:
            status[name] = {"status": "error", "count": 0, "message": str(exc)}
            continue
        for it in items:
            results.append({**it, "source": name})
        status[name] = {"status": "ok", "count": len(items), "cached": hit}

    # diskon terbesar dulu; yang tanpa angka diskon di belakang
    results.sort(key=lambda d: (d.get("discount_pct") is None, -(d.get("discount_pct") or 0)))
    return {"query": q, "results": results, "sources": status}


def status(include_usage: bool = False) -> dict:
    out = {
        "tracked": {"configured": True},
        "affiliate": {"configured": shopee_graphql.configured()},
        "web": {
            "configured": piloterr.configured(),
            "spent_today": piloterr.spent_today(),
            "daily_limit": settings.piloterr_daily_limit,
        },
    }
    if include_usage and piloterr.configured():
        try:
            out["web"]["usage"] = piloterr.usage()
        except piloterr.PiloterrError as exc:
            out["web"]["usage_error"] = str(exc)
    return out
