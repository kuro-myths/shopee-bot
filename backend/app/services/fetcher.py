"""Price fetcher used by the background checker.

Attempts to read a live price from a product page. Marketplace pages are
heavily protected, so this is best-effort: it parses OpenGraph / meta
tags that are served without JavaScript. Returns None when the page
cannot be read — the extension remains the primary price source.
"""
import re
import urllib.request
from html.parser import HTMLParser

TIMEOUT = 10


class MetaPriceParser(HTMLParser):
    """Collects og:price:amount / product:price:amount meta tags."""

    def __init__(self):
        super().__init__()
        self.prices = []

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        attrs = dict(attrs)
        prop = attrs.get("property") or attrs.get("name") or ""
        if prop in ("og:price:amount", "product:price:amount", "og:price"):
            content = attrs.get("content")
            if content:
                self.prices.append(content)


def _parse_price(text):
    """Parse a price string into a float.

    Handles both Indonesian (1.234.567) and decimal (12.34) notations:
    - commas are always decimal separators
    - a trailing dot followed by 1-2 digits is a decimal separator
    - otherwise dots are thousand separators
    """
    if not text:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)*)", str(text).replace(" ", ""))
    if not m:
        return None
    raw = m.group(1)
    if "," in raw:
        cleaned = raw.replace(".", "").replace(",", ".")
    else:
        parts = raw.split(".")
        if len(parts) > 1 and len(parts[-1]) in (1, 2):
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        else:
            cleaned = raw.replace(".", "")
    try:
        value = float(cleaned)
        return value if value > 0 else None
    except ValueError:
        return None


def fetch_price(url: str):
    """Fetch a product page and return (price, error) best-effort."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PriceDropTracker/0.1)"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read(200_000).decode("utf-8", errors="ignore")
        parser = MetaPriceParser()
        parser.feed(html)
        for raw in parser.prices:
            price = _parse_price(raw)
            if price:
                return price, None
        return None, "no_price_meta"
    except Exception as exc:  # network errors, timeouts, HTTP errors
        return None, str(exc)
