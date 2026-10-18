"""Background price checker.

Runs a daemon thread that periodically re-checks tracked products via
the fetcher and records new price points through the same upsert path
used by the extension (so drop detection and target alerts fire).
"""
import logging
import threading
import time

from ..db import db
from .fetcher import fetch_price

log = logging.getLogger("pricedrop.checker")

DEFAULT_INTERVAL_SECONDS = 6 * 60 * 60  # every 6 hours
MIN_INTERVAL_SECONDS = 60  # never poll faster than once a minute


class PriceChecker:
    def __init__(self, interval_seconds: int = DEFAULT_INTERVAL_SECONDS):
        self.interval = max(int(interval_seconds), MIN_INTERVAL_SECONDS)
        self._consecutive_failures = 0
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="price-checker", daemon=True)
        self._thread.start()
        log.info("Price checker started (interval=%ss)", self.interval)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        log.info("Price checker stopped")

    def _run(self):
        while not self._stop.is_set():
            try:
                self.check_all()
            except Exception:
                log.exception("Price check cycle failed")
            self._stop.wait(self.interval)

    def check_all(self):
        """Fetch prices for all tracked products and record them."""
        with db() as conn:
            products = conn.execute(
                "SELECT * FROM products WHERE archived = 0"
            ).fetchall()
        if not products:
            log.info("No products to check")
            return 0

        checked = 0
        failures = 0
        for product in products:
            if self._stop.is_set():
                break
            price, error = fetch_price(product["url"])
            if price is not None:
                self._record_price(product["id"], price)
                checked += 1
                self._consecutive_failures = 0
            else:
                failures += 1
                self._consecutive_failures += 1
                log.info("Skip %s: %s", product["url"], error or "no price")

        if failures:
            log.warning(
                "Check cycle done: %d updated, %d skipped (consecutive failures=%d)",
                checked,
                failures,
                self._consecutive_failures,
            )
        return checked

    def _record_price(self, product_id: int, price: float):
        """Record a price point and trigger drop/target notifications."""
        # Reuse the same logic as the API by calling the router function
        from ..routers.products import upsert_product
        from ..models import ProductIn

        with db() as conn:
            row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not row:
            return
        upsert_product(
            ProductIn(
                url=row["url"],
                name=row["name"],
                marketplace=row["marketplace"],
                image=row["image"],
                current_price=price,
            )
        )


checker = PriceChecker()
