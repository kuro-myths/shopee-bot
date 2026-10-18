"""Klien Piloterr (https://piloterr.com) - API data web.

Autentikasi: header `x-api-key`. Akun gratis = 50 kredit sekali pakai, jadi
semua panggilan dibatasi harian (PILOTERR_DAILY_LIMIT) dan hasilnya di-cache
oleh lapisan promo. API key tidak pernah di-log atau dikembalikan ke klien.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from ..config import settings

BASE = "https://piloterr.com/api"
TIMEOUT = 25
_spent = {"day": "", "n": 0}


class PiloterrError(Exception):
    def __init__(self, message, kind="http", status=None):
        super().__init__(message)
        self.kind = kind  # auth | credits | rate | limit | config | network | http
        self.status = status


def configured() -> bool:
    return bool(settings.piloterr_api_key)


def _open(req, timeout):  # dipisah agar mudah di-mock pada tes
    return urllib.request.urlopen(req, timeout=timeout)


def _today():
    return time.strftime("%Y-%m-%d")


def spent_today() -> int:
    return _spent["n"] if _spent["day"] == _today() else 0


def _reserve():
    if _spent["day"] != _today():
        _spent["day"], _spent["n"] = _today(), 0
    if _spent["n"] >= settings.piloterr_daily_limit:
        raise PiloterrError(
            f"Batas harian Piloterr tercapai ({settings.piloterr_daily_limit}). Naikkan PILOTERR_DAILY_LIMIT jika perlu.",
            kind="limit",
        )
    _spent["n"] += 1


def _get(path: str, params: dict | None = None, count: bool = True):
    if not configured():
        raise PiloterrError("PILOTERR_API_KEY belum diisi", kind="config")
    if count:
        _reserve()
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"x-api-key": settings.piloterr_api_key, "Accept": "application/json"})
    try:
        with _open(req, TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        kind = {401: "auth", 402: "credits", 429: "rate"}.get(exc.code, "http")
        msg = {
            "auth": "API key Piloterr ditolak (401). Periksa PILOTERR_API_KEY.",
            "credits": "Kredit Piloterr habis (402). Isi ulang atau upgrade di dashboard Piloterr.",
            "rate": "Kuota Piloterr terlampaui (429). Coba lagi nanti.",
        }.get(kind, f"Piloterr mengembalikan HTTP {exc.code}")
        raise PiloterrError(msg, kind=kind, status=exc.code) from None
    except Exception as exc:
        raise PiloterrError(f"Tidak bisa menghubungi Piloterr: {type(exc).__name__}", kind="network") from None
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def usage():
    """Sisa kredit/pemakaian akun (tidak dihitung ke batas harian lokal)."""
    return _get("/usage", count=False)


def _find_results(data):
    """Cari daftar hasil pencarian dengan toleran terhadap bentuk respons."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data
    if isinstance(data, dict):
        for key in ("results", "organic_results", "organic", "items", "data"):
            v = data.get(key)
            found = _find_results(v) if v is not None else None
            if found:
                return found
        for v in data.values():
            if isinstance(v, (list, dict)):
                found = _find_results(v)
                if found and any(("title" in r and ("url" in r or "link" in r)) for r in found):
                    return found
    return None


def google_search(query: str, limit: int = 10) -> list:
    """Pencarian Google via Piloterr -> [{title, url, snippet}]."""
    data = _get("/v2/google/search", {"query": query})
    rows = _find_results(data) or []
    out = []
    for r in rows[:limit]:
        title = r.get("title") or ""
        url = r.get("url") or r.get("link") or ""
        if title and url:
            out.append({"title": title, "url": url, "snippet": r.get("snippet") or r.get("description") or ""})
    return out
